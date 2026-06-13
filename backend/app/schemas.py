from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ── Auth Schemas ─────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str = "User"  # "User", "Owner", "Admin"


class UserOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str = "User"
    is_admin: bool = False
    is_active: bool = True
    created_at: datetime


# ── Review Schemas ───────────────────────────────────────────

class ReviewIn(BaseModel):
    text: Optional[str]
    rating: Optional[int]


class ReviewOut(BaseModel):
    id: int
    user_id: Optional[int]
    product_id: Optional[int] = None
    text: Optional[str]
    rating: Optional[int]
    verdict: Optional[str]
    confidence: Optional[float]
    genuine_probability: Optional[float]
    fusion_strategy: Optional[str]
    created_at: datetime
    flagged: Optional[bool] = False
    flag_count: Optional[int] = 0
    last_flagged_at: Optional[datetime] = None
    flag_reason: Optional[str] = None
    reasoning: Optional[str] = None  # JSON string with modal scores and signals


class AuditLogOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    actor_user_id: Optional[int] = None
    actor_username: Optional[str] = None   # resolved by the endpoint
    action: str
    target_review_id: Optional[int] = None
    target_order_id: Optional[int] = None  # for order-related events
    details: Optional[str] = None
    created_at: datetime


class AuditLogPage(BaseModel):
    items: list[AuditLogOut]
    total: int
    page: int
    page_size: int


# ── Product Schemas ──────────────────────────────────────────

class ProductCreate(BaseModel):
    name: str
    category: str
    price: float
    description: Optional[str] = None
    keywords: Optional[str] = None


class ProductOut(BaseModel):
    id: int
    name: str
    category: str
    price: float
    description: Optional[str] = None
    keywords: Optional[str] = None
    image_filename: Optional[str] = None
    added_by: Optional[int] = None
    is_active: bool
    created_at: datetime
    avg_rating: Optional[float] = None
    review_count: Optional[int] = 0
    fake_count: Optional[int] = 0
    genuine_count: Optional[int] = 0


# ── Cart Schemas ─────────────────────────────────────────────

class CartItemOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    price: float
    quantity: int
    added_at: datetime


class CartOut(BaseModel):
    items: List[CartItemOut]
    total: float


# ── Order Schemas ────────────────────────────────────────────

class OrderCreate(BaseModel):
    payment_method: str = "card"


class OrderItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    price_at_purchase: float
    product_name: Optional[str] = None

class OrderOut(BaseModel):
    id: int
    user_id: int
    total_amount: float
    payment_method: str
    status: str
    ordered_at: datetime
    buyer_username: Optional[str] = None
    items: Optional[list] = None


# ── Upload Batch Schemas ─────────────────────────────────────

class UploadBatchOut(BaseModel):
    id: int
    uploaded_by: int
    filename: str
    total_rows: int
    success_rows: int
    failed_rows: int
    status: str
    uploaded_at: datetime
    completed_at: Optional[datetime] = None
    error_summary: Optional[str] = None
