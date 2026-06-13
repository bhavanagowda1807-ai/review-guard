from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


# ── Existing Models ──────────────────────────────────────────

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: Optional[str] = Field(default=None, unique=True)
    full_name: Optional[str] = None
    hashed_password: str
    role: str = Field(default="User")  # "User", "Owner", "Admin"
    is_admin: bool = Field(default=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None


class Review(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    product_id: Optional[int] = Field(default=None, foreign_key="product.id")
    text: Optional[str] = None
    rating: Optional[int] = None
    verdict: Optional[str] = None
    confidence: Optional[float] = None
    genuine_probability: Optional[float] = None
    fusion_strategy: Optional[str] = None
    # ── Reasoning: JSON blob storing per-modality scores and top signals ──
    reasoning: Optional[str] = None  # JSON string
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # flagging / moderation
    flagged: bool = Field(default=False)
    flag_count: int = Field(default=0)
    last_flagged_at: Optional[datetime] = None
    flag_reason: Optional[str] = None


class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    actor_user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    actor_username: Optional[str] = None          # denormalized for easy display
    action: str
    target_review_id: Optional[int] = Field(default=None, foreign_key="review.id")
    target_order_id: Optional[int] = Field(default=None, foreign_key="order.id")
    details: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── New Models from ReviewGuard ──────────────────────────────

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    category: str
    price: float
    description: Optional[str] = None
    keywords: Optional[str] = None
    image_filename: Optional[str] = None
    added_by: Optional[int] = Field(default=None, foreign_key="user.id")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CartItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    product_id: int = Field(foreign_key="product.id")
    quantity: int = Field(default=1)
    added_at: datetime = Field(default_factory=datetime.utcnow)


class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    total_amount: float
    payment_method: str = Field(default="card")
    status: str = Field(default="pending")  # pending, completed, cancelled
    ordered_at: datetime = Field(default_factory=datetime.utcnow)


class OrderItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id")
    product_id: int = Field(foreign_key="product.id")
    quantity: int
    price_at_purchase: float


class UploadBatch(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    uploaded_by: int = Field(foreign_key="user.id")
    filename: str
    total_rows: int = Field(default=0)
    success_rows: int = Field(default=0)
    failed_rows: int = Field(default=0)
    status: str = Field(default="pending")  # pending, processing, completed, failed
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_summary: Optional[str] = None
