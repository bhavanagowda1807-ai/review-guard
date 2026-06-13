"""
api/shop.py — Shop, Cart, Orders, Product Reviews
Merged from ReviewGuard into the FastAPI backend
"""
import os, csv, io, json
import httpx
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.db import get_db
from app.models import Product, CartItem, Order, OrderItem, Review, UploadBatch, User, AuditLog
from app.api.inference import _build_reasoning
from app.schemas import (
    ProductCreate, ProductOut, CartItemOut, CartOut,
    OrderCreate, OrderOut, UploadBatchOut, ReviewOut
)
from app.api.auth import get_current_user, get_optional_user, require_owner_user

router = APIRouter()


# ── Products ─────────────────────────────────────────────────

@router.get("/products", response_model=List[ProductOut])
async def list_products(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Product).where(Product.is_active == True)
    if category:
        query = query.where(Product.category == category)
    query = query.order_by(desc(Product.created_at))
    result = await db.execute(query)
    products = result.scalars().all()

    out = []
    for p in products:
        # Count reviews
        rev_result = await db.execute(
            select(func.count(), func.avg(Review.rating))
            .where(Review.product_id == p.id)
        )
        count, avg_rating = rev_result.one()
        fake_result = await db.execute(
            select(func.count()).where(Review.product_id == p.id, Review.verdict == "fake")
        )
        fake_count = fake_result.scalar_one()
        genuine_result = await db.execute(
            select(func.count()).where(Review.product_id == p.id, Review.verdict == "genuine")
        )
        genuine_count = genuine_result.scalar_one()

        out.append(ProductOut(
            id=p.id, name=p.name, category=p.category, price=p.price,
            description=p.description, keywords=p.keywords,
            image_filename=p.image_filename, added_by=p.added_by,
            is_active=p.is_active, created_at=p.created_at,
            avg_rating=round(avg_rating, 2) if avg_rating else None,
            review_count=count or 0,
            fake_count=fake_count or 0,
            genuine_count=genuine_count or 0,
        ))
    return out


@router.get("/products/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/products", response_model=ProductOut)
async def create_product(
    name: str = Form(...),
    category: str = Form(...),
    price: float = Form(...),
    description: Optional[str] = Form(None),
    keywords: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_owner_user)
):
    image_filename = None
    if image and image.filename:
        upload_dir = "static/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        image_filename = f"{datetime.utcnow().timestamp()}_{image.filename}"
        with open(os.path.join(upload_dir, image_filename), "wb") as f:
            f.write(await image.read())

    product = Product(
        name=name, category=category, price=price,
        description=description, keywords=keywords,
        image_filename=image_filename, added_by=user.id
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.patch("/products/{product_id}")
async def update_product(
    product_id: int,
    name: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    description: Optional[str] = Form(None),
    keywords: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_owner_user)
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if name is not None:       product.name = name
    if category is not None:   product.category = category
    if price is not None:      product.price = price
    if description is not None: product.description = description
    if keywords is not None:   product.keywords = keywords
    await db.commit()
    await db.refresh(product)
    return product


@router.patch("/products/{product_id}/toggle")
async def toggle_product_status(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_owner_user)
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.is_active = not product.is_active
    await db.commit()
    return {"detail": f"Product {'activated' if product.is_active else 'deactivated'}", "is_active": product.is_active}


@router.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_owner_user)
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.is_active = False
    await db.commit()
    return {"detail": "Product deactivated"}


@router.get("/products/{product_id}/reviews", response_model=List[ReviewOut])
async def get_product_reviews(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Review).where(Review.product_id == product_id)
        .order_by(desc(Review.created_at))
    )
    return result.scalars().all()


# ── Cart ──────────────────────────────────────────────────────

@router.get("/cart", response_model=CartOut)
async def get_cart(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(
        select(CartItem, Product)
        .join(Product, CartItem.product_id == Product.id)
        .where(CartItem.user_id == user.id)
    )
    rows = result.all()
    items = [
        CartItemOut(
            id=cart.id, product_id=cart.product_id,
            product_name=prod.name, price=prod.price,
            quantity=cart.quantity, added_at=cart.added_at
        )
        for cart, prod in rows
    ]
    total = sum(i.price * i.quantity for i in items)
    return CartOut(items=items, total=round(total, 2))


@router.post("/cart/{product_id}")
async def add_to_cart(
    product_id: int,
    quantity: int = Form(default=1),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    # Check product exists
    result = await db.execute(select(Product).where(Product.id == product_id, Product.is_active == True))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check if already in cart
    existing = await db.execute(
        select(CartItem).where(CartItem.user_id == user.id, CartItem.product_id == product_id)
    )
    cart_item = existing.scalar_one_or_none()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(user_id=user.id, product_id=product_id, quantity=quantity)
        db.add(cart_item)

    await db.commit()
    return {"detail": "Added to cart"}


@router.delete("/cart/{product_id}")
async def remove_from_cart(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    result = await db.execute(
        select(CartItem).where(CartItem.user_id == user.id, CartItem.product_id == product_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not in cart")
    await db.delete(item)
    await db.commit()
    return {"detail": "Removed from cart"}


# ── Orders ────────────────────────────────────────────────────

@router.post("/orders", response_model=OrderOut)
async def place_order(
    payment_method: str = Form(default="card"),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    # Get cart
    result = await db.execute(
        select(CartItem, Product)
        .join(Product, CartItem.product_id == Product.id)
        .where(CartItem.user_id == user.id)
    )
    rows = result.all()
    if not rows:
        raise HTTPException(status_code=400, detail="Cart is empty")

    total = sum(prod.price * cart.quantity for cart, prod in rows)

    # Create order — starts at 'pending', owner advances through the flow
    order = Order(user_id=user.id, total_amount=round(total, 2), payment_method=payment_method, status="pending")
    db.add(order)
    await db.flush()

    # Create order items
    for cart, prod in rows:
        order_item = OrderItem(
            order_id=order.id, product_id=prod.id,
            quantity=cart.quantity, price_at_purchase=prod.price
        )
        db.add(order_item)
        await db.delete(cart)

    await db.commit()
    await db.refresh(order)
    return order


@router.get("/orders", response_model=List[OrderOut])
async def list_orders(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(
        select(Order).where(Order.user_id == user.id).order_by(desc(Order.ordered_at))
    )
    orders = result.scalars().all()
    out = []
    for order in orders:
        items_result = await db.execute(
            select(OrderItem, Product).join(Product, Product.id == OrderItem.product_id)
            .where(OrderItem.order_id == order.id)
        )
        items = [
            {"id": oi.id, "product_id": oi.product_id, "quantity": oi.quantity,
             "price_at_purchase": oi.price_at_purchase, "product_name": p.name}
            for oi, p in items_result.all()
        ]
        out.append({"id": order.id, "user_id": order.user_id,
                    "total_amount": order.total_amount, "payment_method": order.payment_method,
                    "status": order.status, "ordered_at": order.ordered_at, "items": items})
    return out


# ── Owner: all orders ─────────────────────────────────────────

@router.get("/owner/orders", response_model=None)
async def owner_list_orders(db: AsyncSession = Depends(get_db), user=Depends(require_owner_user)):
    result = await db.execute(select(Order).order_by(desc(Order.ordered_at)))
    orders = result.scalars().all()
    out = []
    for order in orders:
        items_result = await db.execute(
            select(OrderItem, Product).join(Product, Product.id == OrderItem.product_id)
            .where(OrderItem.order_id == order.id)
        )
        items = [
            {"id": oi.id, "product_id": oi.product_id, "quantity": oi.quantity,
             "price_at_purchase": oi.price_at_purchase, "product_name": p.name}
            for oi, p in items_result.all()
        ]
        # get buyer username
        buyer_result = await db.execute(select(User).where(User.id == order.user_id))
        buyer = buyer_result.scalar_one_or_none()
        out.append({
            "id": order.id, "user_id": order.user_id,
            "buyer_username": buyer.username if buyer else "unknown",
            "total_amount": order.total_amount, "payment_method": order.payment_method,
            "status": order.status, "ordered_at": order.ordered_at, "items": items
        })
    return out


# ── Order status flow: pending → processing → shipped → delivered ──
_OWNER_TRANSITIONS = {
    "pending":    "processing",
    "processing": "shipped",
    "shipped":    "delivered",
}

@router.post("/orders/{order_id}/advance", response_model=None)
async def advance_order_status(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_owner_user)
):
    """Advance an order to its next status in the pipeline."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    current = (order.status or "pending").lower()
    next_status = _OWNER_TRANSITIONS.get(current)
    if not next_status:
        raise HTTPException(
            status_code=400,
            detail=f"Order is already '{order.status}' — no further advancement possible."
        )

    order.status = next_status
    audit = AuditLog(
        actor_user_id=getattr(user, 'id', None),
        actor_username=getattr(user, 'username', None),
        action=f'order_status_changed_to_{next_status}',
        target_order_id=order.id,
        details=json.dumps({'order_id': order.id, 'from': current, 'to': next_status}),
    )
    db.add(audit)
    await db.commit()
    return {"detail": f"Order advanced to '{next_status}'", "status": next_status}


@router.post("/orders/{order_id}/deliver", response_model=None)
async def mark_order_delivered(order_id: int, db: AsyncSession = Depends(get_db), user=Depends(require_owner_user)):
    """Legacy endpoint — jumps directly to delivered."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = "delivered"
    await db.commit()
    return {"detail": "Order marked as delivered"}


@router.post("/orders/{order_id}/cancel", response_model=None)
async def cancel_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    """Customer cancels their own order (only allowed while pending or processing)."""
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.user_id == user.id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    cancellable = {"pending", "processing"}
    if (order.status or "").lower() not in cancellable:
        raise HTTPException(
            status_code=400,
            detail=f"Orders that are '{order.status}' cannot be cancelled."
        )

    order.status = "cancelled"
    audit = AuditLog(
        actor_user_id=getattr(user, 'id', None),
        actor_username=getattr(user, 'username', None),
        action='order_cancelled_by_customer',
        target_order_id=order.id,
        details=json.dumps({'order_id': order.id, 'cancelled_from': (order.status or 'unknown')}),
    )
    db.add(audit)
    await db.commit()
    return {"detail": "Order cancelled successfully"}


# ── Owner: products list ──────────────────────────────────────

@router.get("/owner/products")
async def owner_list_products(db: AsyncSession = Depends(get_db), user=Depends(require_owner_user)):
    """Returns all products with review counts — for the owner's product management table."""
    result = await db.execute(select(Product).order_by(desc(Product.created_at)))
    products = result.scalars().all()
    out = []
    for p in products:
        counts = await db.execute(
            select(
                func.count(Review.id).label("total"),
                func.sum((Review.verdict == "fake").cast(type_=type(1))).label("fake"),
            ).where(Review.product_id == p.id)
        )
        row = counts.one()
        out.append({
            "id": p.id, "name": p.name, "category": p.category,
            "price": p.price, "description": p.description,
            "keywords": p.keywords, "image_filename": p.image_filename,
            "is_active": p.is_active, "added_by": p.added_by,
            "created_at": p.created_at,
            "review_count": row.total or 0,
            "fake_count": int(row.fake or 0),
        })
    return out


# ── Owner: all reviews (read-only) ────────────────────────────

@router.get("/owner/reviews")
async def owner_list_reviews(
    verdict: Optional[str] = None,
    limit: int = 2000,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_owner_user),
):
    """Read-only view of all reviews. Owners cannot delete — use this endpoint only for display."""
    # Show customer reviews only (exclude admin/owner submitted reviews)
    non_customer_ids = select(User.id).where(
        (User.is_admin == True) | (User.role == 'Owner')
    )
    query = select(Review).where(Review.user_id.not_in(non_customer_ids))
    if verdict in ("fake", "genuine", "pending"):
        query = query.where(Review.verdict == verdict)
    query = query.order_by(desc(Review.created_at)).limit(limit)
    result = await db.execute(query)
    reviews = result.scalars().all()

    out = []
    for r in reviews:
        product_name = None
        if r.product_id:
            pr = await db.execute(select(Product).where(Product.id == r.product_id))
            p = pr.scalar_one_or_none()
            product_name = p.name if p else None
        user_result = await db.execute(select(User).where(User.id == r.user_id)) if r.user_id else None
        reviewer = user_result.scalar_one_or_none() if user_result else None
        out.append({
            "id": r.id, "text": r.text, "rating": r.rating,
            "verdict": r.verdict, "confidence": r.confidence,
            "genuine_probability": r.genuine_probability,
            "fusion_strategy": r.fusion_strategy,
            "reasoning": r.reasoning,
            "created_at": r.created_at,
            "product_name": product_name,
            "username": reviewer.username if reviewer else None,
            "flagged": r.flagged, "flag_count": r.flag_count,
            "flag_reason": r.flag_reason if hasattr(r, "flag_reason") else None,
        })
    return out


# ── Owner: stats dashboard ────────────────────────────────────

@router.get("/owner/stats")
async def owner_stats(db: AsyncSession = Depends(get_db), user=Depends(require_owner_user)):
    """Aggregated stats for owner overview KPIs — counts customer reviews only (excludes admin/owner)."""
    product_count = (await db.execute(select(func.count(Product.id)).where(Product.is_active == True))).scalar() or 0

    # Exclude reviews by admin or owner users — same filter as /owner/reviews
    non_customer_ids = select(User.id).where(
        (User.is_admin == True) | (User.role == 'Owner')
    )
    customer_reviews = select(func.count(Review.id)).where(Review.user_id.not_in(non_customer_ids))
    total_reviews = (await db.execute(customer_reviews)).scalar() or 0
    genuine_count = (await db.execute(customer_reviews.where(Review.verdict == "genuine"))).scalar() or 0
    fake_count    = (await db.execute(customer_reviews.where(Review.verdict == "fake"))).scalar() or 0
    pending_count = (await db.execute(customer_reviews.where(Review.verdict == None))).scalar() or 0

    total_orders  = (await db.execute(select(func.count(Order.id)))).scalar() or 0
    pending_orders = (await db.execute(select(func.count(Order.id)).where(Order.status == "pending"))).scalar() or 0
    return {
        "products": product_count,
        "total": total_reviews,
        "genuine": genuine_count,
        "fake": fake_count,
        "pending": pending_count,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
    }

@router.get("/user/metadata")
async def get_user_metadata(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """
    Auto-computes 10 metadata features from real account activity.
    Used by the ML inference service to classify review authenticity.
    """
    from datetime import datetime, timedelta
    import math

    account_age = max((datetime.utcnow() - user.created_at).days, 1)

    reviews_result = await db.execute(
        select(Review).where(Review.user_id == user.id).order_by(Review.created_at)
    )
    reviews = reviews_result.scalars().all()
    total_reviews = len(reviews)
    reviews_per_day = round(total_reviews / account_age, 4)

    orders_result = await db.execute(select(Order).where(Order.user_id == user.id))
    orders = orders_result.scalars().all()
    verified_purchase_ratio = round(len(orders) / max(total_reviews, 1), 4)

    avg_rating = sum(r.rating or 3 for r in reviews) / max(total_reviews, 1)
    rating_deviation = round(abs(avg_rating - 3.5), 4)

    burstiness = 0.0
    if total_reviews > 1:
        dates = sorted([r.created_at for r in reviews if r.created_at])
        max_in_window = 1
        for d in dates:
            window_end = d + timedelta(days=7)
            count = sum(1 for dd in dates if d <= dd <= window_end)
            max_in_window = max(max_in_window, count)
        burstiness = round(max_in_window / max(account_age / 7, 1), 4)

    helpful_count = sum(1 for r in reviews if getattr(r, 'helpful_votes', 0) and r.helpful_votes > 0)
    helpfulness_ratio = round(helpful_count / max(total_reviews, 1), 4)

    # ── Feature 7: similarity_score ──────────────────────────────
    # Measure lexical overlap between this user's review texts
    # High overlap = copy-paste behavior = fake signal
    similarity_score = 0.0
    texts = [r.text or r.body or '' for r in reviews if (r.text or getattr(r, 'body', ''))]
    if len(texts) >= 2:
        def word_set(t): return set(t.lower().split())
        overlaps = []
        for i in range(min(len(texts), 10)):
            for j in range(i + 1, min(len(texts), 10)):
                a, b = word_set(texts[i]), word_set(texts[j])
                if a and b:
                    overlaps.append(len(a & b) / math.sqrt(len(a) * len(b)))
        similarity_score = round(sum(overlaps) / max(len(overlaps), 1), 4) if overlaps else 0.0

    # ── Feature 8: sentiment_rating_mismatch ─────────────────────
    # Count reviews where short exclamatory text (likely positive)
    # doesn't match the numeric rating — or where negative words appear with 5 stars
    mismatch_count = 0
    negative_words = {'bad', 'terrible', 'awful', 'horrible', 'worst', 'poor', 'waste',
                      'broken', 'damaged', 'useless', 'disappointed', 'disappointing', 'defective'}
    positive_words = {'great', 'excellent', 'amazing', 'perfect', 'love', 'best', 'awesome',
                      'fantastic', 'wonderful', 'superb', 'outstanding'}
    for r in reviews:
        t = (r.text or getattr(r, 'body', '') or '').lower()
        stars = r.rating or 3
        words = set(t.split())
        neg_hit = bool(words & negative_words)
        pos_hit = bool(words & positive_words)
        if (neg_hit and stars >= 4) or (pos_hit and stars <= 2):
            mismatch_count += 1
    sentiment_rating_mismatch = round(mismatch_count / max(total_reviews, 1), 4)

    # ── Feature 9: night_review_ratio ────────────────────────────
    # Reviews submitted between 1am–5am local time (UTC proxy)
    night_count = sum(
        1 for r in reviews
        if r.created_at and 1 <= r.created_at.hour <= 5
    )
    night_review_ratio = round(night_count / max(total_reviews, 1), 4)

    # ── Feature 10: reviewer_overlap_score ───────────────────────
    # How many products this user reviewed were also reviewed by flagged/fake users
    reviewer_overlap_score = 0.0
    if reviews:
        product_ids = [r.product_id for r in reviews if r.product_id]
        if product_ids:
            # Get all reviews on the same products by OTHER users
            co_reviews_result = await db.execute(
                select(Review.user_id, func.count(Review.id).label('cnt'))
                .where(Review.product_id.in_(product_ids))
                .where(Review.user_id != user.id)
                .group_by(Review.user_id)
            )
            co_reviewers = co_reviews_result.all()
            # Flag: co-reviewers who reviewed 3+ of the same products
            overlap_users = sum(1 for _, cnt in co_reviewers if cnt >= 3)
            reviewer_overlap_score = round(
                min(overlap_users / max(len(product_ids), 1), 1.0), 4
            )

    return {
        "user_id": user.id,
        "username": user.username,
        "account_age": float(account_age),
        "total_reviews": total_reviews,
        "reviews_per_day": reviews_per_day,
        "verified_purchase_ratio": verified_purchase_ratio,
        "rating_deviation": rating_deviation,
        "burstiness": burstiness,
        "helpfulness_ratio": helpfulness_ratio,
        "similarity_score": similarity_score,
        "sentiment_rating_mismatch": sentiment_rating_mismatch,
        "night_review_ratio": night_review_ratio,
        "reviewer_overlap_score": reviewer_overlap_score,
    }

# ── CSV Upload (Admin) ────────────────────────────────────────

@router.post("/upload/reviews")
async def upload_reviews_csv(
    csv_file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    if not getattr(user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Admin required")

    ML_URL = os.getenv("ML_SERVICE_URL", "http://ml_inference:8501").rstrip("/")
    if ML_URL.endswith("/predict"):
        ML_URL = ML_URL[: -len("/predict")]

    raw = await csv_file.read()
    batch = UploadBatch(
        uploaded_by=user.id, filename=csv_file.filename or "upload.csv",
        status="processing"
    )
    db.add(batch)
    await db.flush()

    async def run_inference(client: httpx.AsyncClient, text: str, rating: int, meta: dict = None) -> dict:
        """Call ML service with text + metadata. Falls back gracefully."""
        try:
            data = {
                "text": text,
                "rating": str(rating),
                "fusion_strategy": "attention",
            }
            if meta:
                for k, v in meta.items():
                    if v is not None:
                        data[k] = str(v)
            resp = await client.post(f"{ML_URL}/predict", data=data, timeout=15.0)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return {}

    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8")))
        rows_list = list(reader)
        success, failed = 0, 0
        
        # Prepare all review data first
        tasks = []
        for row in rows_list:
            try:
                text = (
                    row.get("Comment") or row.get("text") or row.get("comment")
                    or row.get("review_text") or row.get("Review") or ""
                ).strip()
                if not text:
                    failed += 1
                    continue

                rating_raw = row.get("Rating") or row.get("rating") or row.get("stars") or "3"
                try:
                    rating = int(float(str(rating_raw).strip()))
                except Exception:
                    rating = 3

                # Label column — determines the ground-truth verdict shown in the table
                label_raw = (
                    row.get("Label") or row.get("label") or row.get("fake")
                    or row.get("is_fake") or row.get("class") or ""
                ).strip()
                if label_raw in ("1", "1.0", "fake", "Fake", "FAKE", "yes", "Yes"):
                    label_verdict = "fake"
                elif label_raw in ("0", "0.0", "genuine", "Genuine", "real", "Real", "no", "No"):
                    label_verdict = "genuine"
                else:
                    label_verdict = None

                # Extract metadata features from CSV row if present
                def _f(row, *keys):
                    for k in keys:
                        v = row.get(k)
                        if v not in (None, ""):
                            try: return float(v)
                            except: pass
                    return None

                meta = {
                    "account_age":               _f(row, "account_age"),
                    "reviews_per_day":           _f(row, "reviews_per_day"),
                    "verified_purchase_ratio":   _f(row, "verified_purchase_ratio"),
                    "rating_deviation":          _f(row, "rating_deviation"),
                    "burstiness":                _f(row, "burstiness"),
                    "helpfulness_ratio":         _f(row, "helpfulness_ratio"),
                    "similarity_score":          _f(row, "similarity_score"),
                    "sentiment_rating_mismatch": _f(row, "sentiment_rating_mismatch"),
                    "night_review_ratio":        _f(row, "night_review_ratio"),
                    "reviewer_overlap_score":    _f(row, "reviewer_overlap_score"),
                }
                tasks.append((text, rating, meta, label_verdict))
            except Exception:
                failed += 1
        
        # Run inference in parallel (max 5 concurrent)
        import asyncio
        async with httpx.AsyncClient(timeout=15.0) as client:
            semaphore = asyncio.Semaphore(5)
            
            async def bounded_inference(text, rating, meta, label_verdict):
                async with semaphore:
                    ml = await run_inference(client, text, rating, meta)
                    ai_verdict = ml.get("verdict")
                    confidence = ml.get("confidence")
                    genuine_prob = ml.get("genuine_probability")
                    verdict = label_verdict if label_verdict else ai_verdict
                    if ml and meta:
                        ml["metadata_features"] = {k: v for k, v in meta.items() if v is not None}
                    reasoning = _build_reasoning(ml) if ml else None
                    return (text, rating, verdict, confidence, genuine_prob, ml.get("fusion_strategy"), reasoning)
            
            results = await asyncio.gather(*[bounded_inference(t, r, m, lv) for t, r, m, lv in tasks], return_exceptions=True)
        
        # Add all results to DB
        for result in results:
            if isinstance(result, Exception):
                failed += 1
                continue
            try:
                text, rating, verdict, confidence, genuine_prob, fusion_strategy, reasoning = result
                review = Review(
                    user_id=user.id,
                    text=text,
                    rating=rating,
                    verdict=verdict,
                    confidence=confidence,
                    genuine_probability=genuine_prob,
                    fusion_strategy=fusion_strategy,
                    reasoning=reasoning,
                )
                db.add(review)
                success += 1
            except Exception:
                failed += 1

        batch.total_rows = success + failed
        batch.success_rows = success
        batch.failed_rows = failed
        batch.status = "completed"
        batch.completed_at = datetime.utcnow()
        await db.commit()
        return {"detail": f"Uploaded {success} reviews, {failed} failed", "batch_id": batch.id}

    except Exception as e:
        batch.status = "failed"
        batch.error_summary = str(e)
        await db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/upload/batches", response_model=List[UploadBatchOut])
async def list_batches(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    if not getattr(user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Admin required")
    result = await db.execute(select(UploadBatch).order_by(desc(UploadBatch.uploaded_at)))
    return result.scalars().all()



@router.get("/rankings")
async def get_rankings(category: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """Products ranked by genuine review ratio (fake reviews excluded from scoring)."""
    query = select(Product).where(Product.is_active == True)
    if category and category != "All":
        query = query.where(Product.category == category)
    result = await db.execute(query)
    products = result.scalars().all()

    ranked = []
    for p in products:
        rev_result = await db.execute(select(Review).where(Review.product_id == p.id))
        reviews = rev_result.scalars().all()
        total = len(reviews)
        genuine = sum(1 for r in reviews if r.verdict == "genuine")
        fake = sum(1 for r in reviews if r.verdict == "fake")
        avg_rating = (sum(r.rating for r in reviews if r.rating) / total) if total else 0
        trust_ratio = (genuine / total) if total > 0 else 0.5
        ranked.append({
            "id": p.id, "name": p.name, "category": p.category,
            "price": p.price, "description": p.description,
            "image_filename": p.image_filename,
            "review_count": total, "genuine_count": genuine, "fake_count": fake,
            "avg_rating": round(avg_rating, 2),
            "trust_ratio": round(trust_ratio, 3),
        })

    ranked.sort(key=lambda x: x["trust_ratio"], reverse=True)
    return ranked


# ── Stats for visualization ───────────────────────────────────

@router.get("/stats/reviews")
async def review_stats(db: AsyncSession = Depends(get_db)):
    """Returns stats for charts: verdict breakdown, per-product counts."""
    fake_count    = (await db.execute(select(func.count()).where(Review.verdict == "fake"))).scalar_one() or 0
    genuine_count = (await db.execute(select(func.count()).where(Review.verdict == "genuine"))).scalar_one() or 0
    total_count   = (await db.execute(select(func.count(Review.id)))).scalar_one() or 0
    pending_count = total_count - fake_count - genuine_count
    flagged_count = (await db.execute(select(func.count()).where(Review.flagged == True))).scalar_one() or 0
    users_count   = (await db.execute(select(func.count()).select_from(__import__('app.models', fromlist=['User']).User))).scalar_one() or 0

    # Avg confidence
    avg_conf_result = await db.execute(select(func.avg(Review.confidence)).where(Review.confidence != None))
    avg_conf = float(avg_conf_result.scalar_one() or 0)

    fake_rate = round((fake_count / total_count * 100), 1) if total_count > 0 else 0

    # Per product stats
    from sqlalchemy import case
    prod_result = await db.execute(
        select(
            Product.name,
            func.count(Review.id),
            func.sum(case((Review.verdict == "fake", 1), else_=0))
        )
        .join(Review, Review.product_id == Product.id, isouter=True)
        .group_by(Product.id, Product.name)
        .limit(10)
    )
    product_stats = [
        {"product": row[0], "total": row[1] or 0, "fake": row[2] or 0}
        for row in prod_result.all()
    ]

    # Reviews by date (last 14 days)
    from datetime import datetime, timedelta
    from sqlalchemy import cast, Date
    date_result = await db.execute(
        select(
            cast(Review.created_at, Date).label("date"),
            func.count(Review.id).label("total"),
            func.sum(case((Review.verdict == "fake", 1), else_=0)).label("fake"),
            func.sum(case((Review.verdict == "genuine", 1), else_=0)).label("genuine"),
        )
        .where(Review.created_at >= datetime.utcnow() - timedelta(days=14))
        .group_by(cast(Review.created_at, Date))
        .order_by(cast(Review.created_at, Date))
    )
    by_date = [
        {"date": str(row.date), "total": row.total or 0, "fake": row.fake or 0, "genuine": row.genuine or 0}
        for row in date_result.all()
    ]

    return {
        "total":       total_count,
        "fake":        fake_count,
        "genuine":     genuine_count,
        "pending":     pending_count,
        "flagged":     flagged_count,
        "fake_rate":   fake_rate,
        "avg_confidence": round(avg_conf * 100, 1),
        "users":       users_count,
        "by_product":  product_stats,
        "by_date":     by_date,
    }
