from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta
from app.database import get_db
from app.models import User, UserRole
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Password utils ─────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# ── Session utils ──────────────────────────────────────────────────────────

def create_session(request: Request, user: User):
    request.session["user_id"]   = user.user_id
    request.session["user_name"] = user.name
    request.session["user_role"] = user.role.value
    request.session["logged_in"] = True
    request.session["login_at"]  = datetime.utcnow().isoformat()

def clear_session(request: Request):
    request.session.clear()

def get_current_user(request: Request):
    if not request.session.get("logged_in"):
        return None
    return {
        "user_id":   request.session.get("user_id"),
        "user_name": request.session.get("user_name"),
        "user_role": request.session.get("user_role"),
    }

def require_login(request: Request):
    user = get_current_user(request)
    if not user:
        from fastapi.responses import RedirectResponse
        raise HTTPException(status_code=302, detail="Not logged in")
    return user

def require_admin(request: Request):
    user = get_current_user(request)
    if not user or user["user_role"] != UserRole.admin.value:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

def require_student(request: Request):
    user = get_current_user(request)
    if not user or user["user_role"] != UserRole.student.value:
        raise HTTPException(status_code=403, detail="Student access required")
    return user

# ── Login attempt tracking (in-memory) ────────────────────────────────────
# tracks failed attempts per email: {email: {"count": int, "locked_until": datetime}}
login_attempts: dict = {}

LOCKOUT_THRESHOLD = 5
LOCKOUT_MINUTES   = 15

def check_lockout(email: str) -> bool:
    """Returns True if account is currently locked."""
    record = login_attempts.get(email)
    if not record:
        return False
    if record["locked_until"] and datetime.utcnow() < record["locked_until"]:
        return True
    return False

def get_lockout_remaining(email: str) -> int:
    """Returns remaining lockout minutes.""" 
    record = login_attempts.get(email)
    if not record or not record.get("locked_until"):
        return 0
    delta = record["locked_until"] - datetime.utcnow()
    return max(0, int(delta.total_seconds() // 60) + 1)

def record_failed_attempt(email: str):
    if email not in login_attempts:
        login_attempts[email] = {"count": 0, "locked_until": None}
    login_attempts[email]["count"] += 1
    if login_attempts[email]["count"] >= LOCKOUT_THRESHOLD:
        login_attempts[email]["locked_until"] = (
            datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
        )

def reset_attempts(email: str):
    if email in login_attempts:
        del login_attempts[email]