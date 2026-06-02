from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Inquiry, InquiryStatus, Product, AuditLog
from app.auth import get_current_user, require_admin

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")  # Siguroha nga naa kini nga linya

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user or user["user_role"] != "admin":
        return RedirectResponse("/login", status_code=302)

    # Stats - Giusab gikan sa 0 ngadto sa False para sa PostgreSQL Boolean Compatibility
    pending_count   = db.query(Inquiry).filter(
        Inquiry.status == InquiryStatus.pending).count()
    
    responded_count = db.query(Inquiry).filter(
        Inquiry.status == InquiryStatus.responded).count()
    
    active_products = db.query(Product).filter(
        Product.is_deleted == False,  # Kani nga linya ang gi-fix
        Product.product_status == "Available").count()
    
    total_products  = db.query(Product).filter(
        Product.is_deleted == False).count()  # Kani pod nga linya ang gi-fix

    # Pending inquiries (latest 5)
    pending_inquiries = (
        db.query(Inquiry)
        .filter(Inquiry.status == InquiryStatus.pending)
        .order_by(Inquiry.created_at.desc())
        .limit(5)
        .all()
    )

    # Recent audit logs (latest 5)
    recent_logs = (
        db.query(AuditLog)
        .order_by(AuditLog.performed_at.desc())
        .limit(5)
        .all()
    )

    return templates.TemplateResponse("admin/dashboard.html", {
        "request":           request,
        "user":              user,
        "pending_count":     pending_count,
        "responded_count":   responded_count,
        "active_products":   active_products,
        "total_products":    total_products,
        "pending_inquiries": pending_inquiries,
        "recent_logs":       recent_logs,
    })
