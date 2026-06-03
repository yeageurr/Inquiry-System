from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
import json  # GIDUGANG: Para sa pag-parse sa JSON data

from app.database import get_db
from app.models import AuditLog
from app.auth import get_current_user

router = APIRouter(prefix="/admin")

# ── GI-FIX 1: Gi-initialize ang templates variable ────────────────────────
templates = Jinja2Templates(directory="app/templates")

# ── GI-FIX 2: Gidugang ang custom filter para sa log.action_details ───────
def from_json_custom(value):
    try:
        return json.loads(value) if value else {}
    except (ValueError, TypeError):
        return {}

# Gi-register ang filter sa Jinja2 environment para mabasa sa HTML template
templates.env.filters["from_json_custom"] = from_json_custom


@router.get("/audit-logs", response_class=HTMLResponse)
async def audit_logs(
    request:     Request,
    action_type: str = "All",
    search:      str = "",
    db:          Session = Depends(get_db)
):
    user = get_current_user(request)
    if not user or user["user_role"] != "admin":
        return RedirectResponse("/login", status_code=302)

    query = (
        db.query(AuditLog)
        .options(joinedload(AuditLog.actor))
    )

    if action_type != "All":
        query = query.filter(AuditLog.action_type == action_type)

    if search:
        query = query.filter(
            AuditLog.action_type.ilike(f"%{search}%") |
            AuditLog.action_details.ilike(f"%{search}%")
        )

    logs = query.order_by(AuditLog.performed_at.desc()).all()

    return templates.TemplateResponse("admin/audit_logs.html", {
        "request":     request,
        "user":        user,
        "logs":        logs,
        "action_type": action_type,
        "search":      search,
    })
