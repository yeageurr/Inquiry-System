from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import json
import os

from app.database import engine, Base
from app.routers import auth, products, inquiries, audit, dashboard

load_dotenv()

# ── Create all tables on startup ───────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── App ────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="IGP Product Inquiry System",
    description="EVSU IGP Office Products and Inquiry System",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url=None
)

# ── Middleware ─────────────────────────────────────────────────────────────
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "changethis"),
    max_age=int(os.getenv("SESSION_EXPIRE_MINUTES", 30)) * 60,
    https_only=False,
    same_site="lax"
)

# ── Static files ───────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")

# ── Custom Jinja2 filters ──────────────────────────────────────────────────
templates = Jinja2Templates(directory="app/templates")

def truncate_details(value):
    try:
        data = json.loads(value)
        parts = []
        for k, v in data.items():
            if not isinstance(v, dict):
                parts.append(str(v))
        return ", ".join(parts[:2]) or str(data)
    except Exception:
        return str(value)[:60] if value else "—"

templates.env.filters["truncate_details"] = truncate_details

# ── Inject templates into routers ──────────────────────────────────────────
dashboard.templates = templates
audit.templates     = templates
products.templates  = templates
inquiries.templates = templates
auth.templates      = templates

# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(products.router)
app.include_router(inquiries.router)
app.include_router(audit.router)