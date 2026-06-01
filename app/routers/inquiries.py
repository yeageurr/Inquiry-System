from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from app.database import get_db
from app.models import (
    Inquiry, InquiryStatus, InquiryResponse,
    EmailStatus, Product, AuditLog, User
)
from app.auth import get_current_user
from app.email import send_email, build_inquiry_response_email
import json

router    = APIRouter()


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

    # Check if product exists and is No Stocks
    product = db.query(Product).filter(
        Product.product_id == product_id,
        Product.is_deleted == 0
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
            joinedload(Inquiry.product),
            joinedload(Inquiry.response)
        )
        .filter(Inquiry.inquiry_id == inquiry_id)
        .first()
    )

    if not inquiry:
        return JSONResponse({"error": "Inquiry not found."}, status_code=404)

    # Check if already responded (and not delivery failed)
    if inquiry.response and inquiry.response.email_status != EmailStatus.failed:
        return JSONResponse(
            {"error": "This inquiry has already been responded to."}, status_code=400)

    # Send email
    email_body = build_inquiry_response_email(
        student_name     = inquiry.student.name,
        product_name     = inquiry.product.product_name,
        response_message = response_message,
        responded_at     = datetime.utcnow().strftime("%B %d, %Y %I:%M %p"),
        inquiry_message  = inquiry.message
    )

    email_sent = await send_email(
        to         = inquiry.student.email,
        subject    = f"Re: Inquiry for {inquiry.product.product_name}",
        body_html  = email_body
    )

    email_status = EmailStatus.delivered if email_sent else EmailStatus.failed

    # Save response
    if inquiry.response:
        # Re-send case
        inquiry.response.response_message = response_message
        inquiry.response.email_status     = email_status
        inquiry.response.responded_at     = datetime.utcnow()
        inquiry.response.admin_id         = user["user_id"]
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

    # Audit log
    log = AuditLog(
        user_id        = user["user_id"],
        action_type    = "SEND_RESPONSE",
        target_id      = str(inquiry_id),
        action_details = json.dumps({
            "student_email": inquiry.student.email,
            "product_name":  inquiry.product.product_name,
            "email_status":  email_status.value
        }),
        performed_at   = datetime.utcnow()
    )
    db.add(log)
    db.commit()

    return JSONResponse({
        "success":      True,
        "email_status": email_status.value,
        "message":      "Response sent successfully." if email_sent
                        else "Response saved but email delivery failed. Will retry."
    })