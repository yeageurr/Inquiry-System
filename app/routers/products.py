from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models import Product, ProductStatus, AuditLog, User
from app.auth import get_current_user
import json

router    = APIRouter()


def log_action(db, user_id, action_type, target_id, details: dict):
    log = AuditLog(
        user_id        = user_id,
        action_type    = action_type,
        target_id      = str(target_id),
        action_details = json.dumps(details),
        performed_at   = datetime.utcnow()
    )
    db.add(log)
    db.commit()


# ── Admin: Product Management ──────────────────────────────────────────────

@router.get("/admin/products", response_class=HTMLResponse)
async def admin_products(
    request: Request,
    search:  str = "",
    status:  str = "All",
    db:      Session = Depends(get_db)
):
    user = get_current_user(request)
    if not user or user["user_role"] != "admin":
        return RedirectResponse("/login", status_code=302)

    query = db.query(Product).filter(Product.is_deleted == 0)

    if status == "Available":
        query = query.filter(Product.product_status == ProductStatus.available)
    elif status == "No Stocks":
        query = query.filter(Product.product_status == ProductStatus.no_stocks)

    if search:
        query = query.filter(Product.product_name.ilike(f"%{search}%"))

    products = query.order_by(Product.date_added.desc()).all()

    return templates.TemplateResponse("admin/products.html", {
        "request":  request,
        "user":     user,
        "products": products,
        "search":   search,
        "status":   status,
    })


@router.post("/admin/products/add")
async def add_product(
    request:             Request,
    product_name:        str = Form(...),
    product_description: str = Form(""),
    product_price:       float = Form(...),
    product_status:      str = Form(...),
    db:                  Session = Depends(get_db)
):
    user = get_current_user(request)
    if not user or user["user_role"] != "admin":
        return JSONResponse({"error": "Unauthorized"}, status_code=403)

    product = Product(
        product_name        = product_name.strip(),
        product_description = product_description.strip() or None,
        product_price       = product_price,
        product_status      = product_status,
        created_by          = user["user_id"],
        date_added          = datetime.utcnow(),
        updated_at          = datetime.utcnow()
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    log_action(db, user["user_id"], "ADD_PRODUCT", product.product_id, {
        "product_name":  product_name,
        "product_price": product_price,
        "status":        product_status
    })

    return RedirectResponse("/admin/products", status_code=302)


@router.post("/admin/products/edit/{product_id}")
async def edit_product(
    request:             Request,
    product_id:          int,
    product_name:        str = Form(...),
    product_description: str = Form(""),
    product_price:       float = Form(...),
    product_status:      str = Form(...),
    db:                  Session = Depends(get_db)
):
    user = get_current_user(request)
    if not user or user["user_role"] != "admin":
        return JSONResponse({"error": "Unauthorized"}, status_code=403)

    product = db.query(Product).filter(
        Product.product_id == product_id,
        Product.is_deleted == 0
    ).first()

    if not product:
        return JSONResponse({"error": "Product not found"}, status_code=404)

    before = {
        "product_name":   product.product_name,
        "product_price":  float(product.product_price),
        "product_status": product.product_status.value
    }

    product.product_name        = product_name.strip()
    product.product_description = product_description.strip() or None
    product.product_price       = product_price
    product.product_status      = product_status
    product.updated_at          = datetime.utcnow()
    db.commit()

    log_action(db, user["user_id"], "EDIT_PRODUCT", product_id, {
        "before": before,
        "after": {
            "product_name":   product_name,
            "product_price":  product_price,
            "product_status": product_status
        }
    })

    return RedirectResponse("/admin/products", status_code=302)


@router.post("/admin/products/delete/{product_id}")
async def delete_product(
    request:    Request,
    product_id: int,
    db:         Session = Depends(get_db)
):
    user = get_current_user(request)
    if not user or user["user_role"] != "admin":
        return JSONResponse({"error": "Unauthorized"}, status_code=403)

    product = db.query(Product).filter(
        Product.product_id == product_id,
        Product.is_deleted == 0
    ).first()

    if not product:
        return JSONResponse({"error": "Product not found"}, status_code=404)

    product.is_deleted = 1
    product.updated_at = datetime.utcnow()
    db.commit()

    log_action(db, user["user_id"], "DELETE_PRODUCT", product_id, {
        "product_name": product.product_name
    })

    return RedirectResponse("/admin/products", status_code=302)


# ── Student: Product Listings ──────────────────────────────────────────────

@router.get("/student/products", response_class=HTMLResponse)
async def student_products(
    request: Request,
    search:  str = "",
    status:  str = "All",
    db:      Session = Depends(get_db)
):
    user = get_current_user(request)
    if not user or user["user_role"] != "student":
        return RedirectResponse("/login", status_code=302)

    query = db.query(Product).filter(Product.is_deleted == 0)

    if status == "Available":
        query = query.filter(Product.product_status == ProductStatus.available)
    elif status == "No Stocks":
        query = query.filter(Product.product_status == ProductStatus.no_stocks)

    if search:
        query = query.filter(Product.product_name.ilike(f"%{search}%"))

    products = query.order_by(Product.date_added.desc()).all()

    return templates.TemplateResponse("student/products.html", {
        "request":  request,
        "user":     user,
        "products": products,
        "search":   search,
        "status":   status,
    })