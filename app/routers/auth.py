from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, UserRole
from app.auth import (
    verify_password, create_session, clear_session,
    check_lockout, record_failed_attempt,
    reset_attempts, get_lockout_remaining, get_current_user
)

router    = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    user = get_current_user(request)
    if user:
        if user["user_role"] == UserRole.admin.value:
            return RedirectResponse("/admin/dashboard", status_code=302)
        return RedirectResponse("/student/products", status_code=302)
    return RedirectResponse("/login", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None):
    user = get_current_user(request)
    if user:
        if user["user_role"] == UserRole.admin.value:
            return RedirectResponse("/admin/dashboard", status_code=302)
        return RedirectResponse("/student/products", status_code=302)
    return templates.TemplateResponse("auth/login.html", {
        "request": request,
        "error":   error
    })


@router.post("/login", response_class=HTMLResponse)
async def login_post(
    request:  Request,
    email:    str = Form(...),
    password: str = Form(...),
    db:       Session = Depends(get_db)
):
    # Check lockout
    if check_lockout(email):
        remaining = get_lockout_remaining(email)
        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "error": f"Account is locked. Try again in {remaining} minute(s)."
        })

    # Find user
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.password):
        record_failed_attempt(email)
        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "error": "Invalid email or password."
        })

    if not user.is_active:
        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "error": "Your account has been deactivated. Please contact the administrator."
        })

    # Success
    reset_attempts(email)
    create_session(request, user)

    if user.role == UserRole.admin:
        return RedirectResponse("/admin/dashboard", status_code=302)
    return RedirectResponse("/student/products", status_code=302)


@router.get("/logout")
async def logout(request: Request):
    clear_session(request)
    return RedirectResponse("/login", status_code=302)