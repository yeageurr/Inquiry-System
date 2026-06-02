import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Text, Enum,
    DateTime, ForeignKey, DECIMAL, Boolean  # Gidugang ang Boolean diri
)
from sqlalchemy.orm import relationship
from app.database import Base


# ── Enums ──────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    student = "student"
    admin   = "admin"

class ProductStatus(str, enum.Enum):
    available = "Available"
    no_stocks = "No Stocks"

class InquiryStatus(str, enum.Enum):
    pending    = "Pending"
    responded  = "Responded"
    closed     = "Closed"

class EmailStatus(str, enum.Enum):
    sent      = "Sent"
    delivered = "Delivered"
    failed    = "Failed"

class ActionType(str, enum.Enum):
    add_product     = "ADD_PRODUCT"
    edit_product    = "EDIT_PRODUCT"
    delete_product  = "DELETE_PRODUCT"
    send_response   = "SEND_RESPONSE"


# ── Models ─────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    user_id    = Column(String(50),  primary_key=True, index=True)
    name       = Column(String(100), nullable=False)
    email      = Column(String(150), unique=True, nullable=False, index=True)
    password   = Column(String(255), nullable=False)
    role       = Column(Enum(UserRole), nullable=False, default=UserRole.student)
    is_active  = Column(Boolean, nullable=False, default=True)  # Gi-ilisgan og Boolean gikan sa TINYINT
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    inquiries          = relationship("Inquiry", back_populates="student",
                                      foreign_keys="Inquiry.user_id")
    inquiry_responses  = relationship("InquiryResponse", back_populates="admin",
                                      foreign_keys="InquiryResponse.admin_id")
    products_created   = relationship("Product", back_populates="creator",
                                      foreign_keys="Product.created_by")
    audit_logs         = relationship("AuditLog", back_populates="actor")


class Product(Base):
    __tablename__ = "products"

    product_id          = Column(Integer, primary_key=True, autoincrement=True, index=True)
    product_name        = Column(String(200),  nullable=False)
    product_description = Column(Text,         nullable=True)
    product_status      = Column(Enum(ProductStatus), nullable=False,
                                 default=ProductStatus.available)
    product_price       = Column(DECIMAL(10, 2), nullable=False)
    is_deleted          = Column(Boolean, nullable=False, default=False)  # Gi-ilisgan og Boolean gikan sa TINYINT
    created_by          = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    date_added          = Column(DateTime, default=datetime.utcnow)
    updated_at          = Column(DateTime, default=datetime.utcnow,
                                 onupdate=datetime.utcnow)

    creator    = relationship("User",    back_populates="products_created",
                              foreign_keys=[created_by])
    inquiries  = relationship("Inquiry", back_populates="product")


class Inquiry(Base):
    __tablename__ = "inquiries"

    inquiry_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id    = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    product_id = Column(Integer,    ForeignKey("products.product_id"), nullable=False)
    message    = Column(Text,       nullable=False)
    status     = Column(Enum(InquiryStatus), nullable=False,
                        default=InquiryStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    student  = relationship("User",    back_populates="inquiries",
                            foreign_keys=[user_id])
    product  = relationship("Product", back_populates="inquiries")
    response = relationship("InquiryResponse", back_populates="inquiry",
                            uselist=False)


class InquiryResponse(Base):
    __tablename__ = "inquiry_responses"

    response_id      = Column(Integer, primary_key=True, autoincrement=True)
    inquiry_id       = Column(Integer, ForeignKey("inquiries.inquiry_id"),
                              nullable=False, unique=True)
    admin_id         = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    response_message = Column(Text, nullable=False)
    email_status     = Column(Enum(EmailStatus), nullable=False,
                              default=EmailStatus.sent)
    responded_at     = Column(DateTime, default=datetime.utcnow)

    inquiry = relationship("Inquiry",  back_populates="response")
    admin   = relationship("User",     back_populates="inquiry_responses",
                           foreign_keys=[admin_id])


class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id        = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    action_type    = Column(String(50), nullable=False)
    target_id      = Column(String(50), nullable=True)
    action_details = Column(Text, nullable=True)
    performed_at   = Column(DateTime, default=datetime.utcnow, index=True)

    actor = relationship("User", back_populates="audit_logs")
