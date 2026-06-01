from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
from app.models import UserRole, ProductStatus, InquiryStatus, EmailStatus


# ── Auth ───────────────────────────────────────────────────────────────────

class LoginForm(BaseModel):
    email:    EmailStr
    password: str


# ── User ───────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    user_id:    str
    name:       str
    email:      str
    role:       UserRole
    is_active:  int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Product ────────────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    product_name:        str
    product_description: Optional[str] = None
    product_status:      ProductStatus
    product_price:       float

    @field_validator("product_price")
    @classmethod
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Price must be a positive number.")
        return v

    @field_validator("product_name")
    @classmethod
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Product name is required.")
        return v.strip()


class ProductUpdate(BaseModel):
    product_name:        Optional[str]           = None
    product_description: Optional[str]           = None
    product_status:      Optional[ProductStatus] = None
    product_price:       Optional[float]         = None


class ProductOut(BaseModel):
    product_id:          int
    product_name:        str
    product_description: Optional[str]
    product_status:      ProductStatus
    product_price:       float
    is_deleted:          int
    date_added:          datetime
    updated_at:          datetime

    class Config:
        from_attributes = True


# ── Inquiry ────────────────────────────────────────────────────────────────

class InquiryCreate(BaseModel):
    product_id: int
    message:    str


class InquiryOut(BaseModel):
    inquiry_id: int
    user_id:    str
    product_id: int
    message:    str
    status:     InquiryStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Inquiry Response ───────────────────────────────────────────────────────

class InquiryResponseCreate(BaseModel):
    response_message: str

    @field_validator("response_message")
    @classmethod
    def message_not_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Response cannot be empty.")
        if len(v) < 10:
            raise ValueError("Response must be at least 10 characters.")
        if len(v) > 1000:
            raise ValueError("Response cannot exceed 1,000 characters.")
        return v


class InquiryResponseOut(BaseModel):
    response_id:      int
    inquiry_id:       int
    admin_id:         str
    response_message: str
    email_status:     EmailStatus
    responded_at:     datetime

    class Config:
        from_attributes = True


# ── Audit Log ──────────────────────────────────────────────────────────────

class AuditLogOut(BaseModel):
    log_id:         int
    user_id:        str
    action_type:    str
    target_id:      Optional[str]
    action_details: Optional[str]
    performed_at:   datetime

    class Config:
        from_attributes = True