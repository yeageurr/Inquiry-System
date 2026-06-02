from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from app.database import get_db, SessionLocal
from app.models import (
    Inquiry, InquiryStatus, InquiryResponse,
    EmailStatus, Product, AuditLog, User
)
from app.email import send_email, build_inquiry_response_email
from app.auth import get_current_user
import json

router    = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# ── Student: Submit Inquiry ────────────────────────────────────────────────

@router.post("/student/inquiries/submit")
async def submit_inquiry(
    request:    Request,
    product_id: int = Form(...),
    message:    str = Form(...),
    db:         Session = Depends(get_db)
):
    user = get_current_user(request)
    if not user or user["user_role"] != "student":
        return JSONResponse({"error": "Unauthorized"}, status_code=403)

    # FIX: Use boolean False instead of integer 0
    product = db.query(Product).filter(
        Product.product_id == product_id,
        Product.is_deleted == False
    ).first()

    if not product:
        return JSONResponse({"error": "Product not found."}, status_code=404)

    if product.product_status.value == "Available":
        return JSONResponse(
            {"error": "This product is currently available. No inquiry needed."},
            status_code=400
        )

    # Check for duplicate pending inquiry
    existing = db.query(Inquiry).filter(
        Inquiry.user_id    == user["user_id"],
        Inquiry.product_id == product_id,
        Inquiry.status     == InquiryStatus.pending
    ).first()

    if existing:
        return JSONResponse(
            {"error": "You already have a pending inquiry for this product."},
            status_code=400
        )

    inquiry = Inquiry(
        user_id    = user["user_id"],
        product_id = product_id,
        message    = message.strip(),
        status     = InquiryStatus.pending,
        created_at = datetime.utcnow(),
        updated_at = datetime.utcnow()
    )
    db.add(inquiry)
    db.commit()

    return JSONResponse({"success": True,
        "message": "Your inquiry has been sent. Please check your email for updates."
    })


# ── Student: My Inquiries ──────────────────────────────────────────────────

@router.get("/student/inquiries", response_class=HTMLResponse)
async def my_inquiries(
    request: Request,
    status:  str = "All",
    db:      Session = Depends(get_db)
):
    user = get_current_user(request)
    if not user or user["user_role"] != "student":
        return RedirectResponse("/login", status_code=302)

    query = (
        db.query(Inquiry)
        .options(
            joinedload(Inquiry.product),
            joinedload(Inquiry.response)
        )
        .filter(Inquiry.user_id == user["user_id"])
    )

    if status != "All":
        query = query.filter(Inquiry.status == status)

    inquiries = query.order_by(Inquiry.created_at.desc()).all()

    return templates.TemplateResponse("student/my_inquiries.html", {
        "request":   request,
        "user":      user,
        "inquiries": inquiries,
        "status":    status,
    })


# ── Admin: Inquiries Management ────────────────────────────────────────────

@router.get("/admin/inquiries", response_class=HTMLResponse)
async def admin_inquiries(
    request: Request,
    status:  str = "All",
    search:  str = "",
    db:      Session = Depends(get_db)
):
    user = get_current_user(request)
    if not user or user["user_role"] != "admin":
        return RedirectResponse("/login", status_code=302)

    query = (
        db.query(Inquiry)
        .options(
            joinedload(Inquiry.student),
            joinedload(Inquiry.product),
            joinedload(Inquiry.response)
        )
    )

    if status != "All":
        query = query.filter(Inquiry.status == status)

    if search:
        query = query.join(Inquiry.student).filter(
            User.name.ilike(f"%{search}%") |
            User.email.ilike(f"%{search}%") |
            Product.product_name.ilike(f"%{search}%")
        )

    inquiries = query.order_by(Inquiry.created_at.desc()).all()

    return templates.TemplateResponse("admin/inquiries.html", {
        "request":   request,
        "user":      user,
        "inquiries": inquiries,
        "status":    status,
        "search":    search,
    })


# ── Admin: Respond to Inquiry ──────────────────────────────────────────────

@router.post("/admin/inquiries/respond/{inquiry_id}")
async def respond_inquiry(
    request:          Request,
    inquiry_id:       int,
    background_tasks: BackgroundTasks, # 1. Gidugang kini nga dependency injection
    response_message: str = Form(...),
    db:               Session = Depends(get_db)
):
    user = get_current_user(request)
    if not user or user["user_role"] != "admin":
        return JSONResponse({"error": "Unauthorized"}, status_code=403)

    # Validate
    response_message = response_message.strip()
    if not response_message:
        return JSONResponse({"error": "Response cannot be empty."}, status_code=400)
    if len(response_message) < 10:
        return JSONResponse(
            {"error": "Response must be at least 10 characters."}, status_code=400)
    if len(response_message) > 1000:
        return JSONResponse(
            {"error": "Response cannot exceed 1,000 characters."}, status_code=400)

    inquiry = (
        db.query(Inquiry)
        .options(
            joinedload(Inquiry.student),
            joinedload(Inquiry.product)
        )
        .filter(Inquiry.inquiry_id == inquiry_id)
        .first()
    )

    if not inquiry:
        return JSONResponse({"error": "Inquiry not found."}, status_code=404)

    existing_response = db.query(InquiryResponse).filter(InquiryResponse.inquiry_id == inquiry_id).first()

    # Kung duna nay malampuson nga tubag kaniadto, dili na usban
    if existing_response and existing_response.email_status.value == EmailStatus.delivered.value:
        return JSONResponse(
            {"error": "This inquiry has already been successfully responded to."}, status_code=400)

    # I-build ang email body daan
    email_body = build_inquiry_response_email(
        student_name     = inquiry.student.name,
        product_name     = inquiry.product.product_name,
        response_message = response_message,
        responded_at     = datetime.utcnow().strftime("%B %d, %Y %I:%M %p"),
        inquiry_message  = inquiry.message
    )

    # 2. DEFAULT STATUS: I-set una nato og "failed" o "pending" samtang wala pa ma-send
    email_status = EmailStatus.failed

    # Pagsalbar sa data sa database (Dali ra kaayo ni, milliseconds ra)
    if existing_response:
        existing_response.response_message = response_message
        existing_response.email_status     = email_status
        existing_response.responded_at     = datetime.utcnow()
        existing_response.admin_id         = user["user_id"]
    else:
        resp = InquiryResponse(
            inquiry_id       = inquiry_id,
            admin_id         = user["user_id"],
            response_message = response_message,
            email_status     = email_status,
            responded_at     = datetime.utcnow()
        )
        db.add(resp)

    # Update inquiry status
    inquiry.status     = InquiryStatus.responded
    inquiry.updated_at = datetime.utcnow()
    db.commit()

    # 3. BACKGROUND TASK SYSTEM: Dinhi na nato ipadagan ang email sa tago
    # Ipadagan ang function sa background, unya i-update ang status kung mapakyas o molusot
    async def email_worker():
        # Maghimo og presko nga db session para sa background worker
        from app.database import SessionLocal
        worker_db = SessionLocal()
        try:
            email_sent = await send_email(
                to        = inquiry.student.email,
                subject   = f"Re: Inquiry for {inquiry.product.product_name}",
                body_html = email_body
            )
            
            # Susiha pag-usab ang response gamit ang worker session aron i-update ang tinuod nga status
            resp_record = worker_db.query(InquiryResponse).filter(InquiryResponse.inquiry_id == inquiry_id).first()
            if resp_record:
                resp_record.email_status = EmailStatus.delivered if email_sent else EmailStatus.failed
                worker_db.commit()
        except Exception as e:
            print(f"[BACKGROUND EMAIL ERROR]: {e}")
        finally:
            worker_db.close()

    # I-salmet sa FastAPI background tasks queue
    background_tasks.add_task(email_worker)

    # Audit log
    log = AuditLog(
        user_id        = user["user_id"],
        action_type    = "SEND_RESPONSE",
        target_id      = str(inquiry_id),
        action_details = json.dumps({
            "student_email": inquiry.student.email,
            "product_name":  inquiry.product.product_name,
            "email_status":  "processing_in_background"
        }),
        performed_at   = datetime.utcnow()
    )
    db.add(log)
    db.commit()

    # 4. INSTANT RESPONSE: Mobalik dayon ni sa Admin dashboard nga walay loading!
    return JSONResponse({
        "success":      True,
        "email_status": "pending",
        "message":      "Response saved! Email is being processed in the background."
    })
