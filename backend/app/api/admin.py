"""
api/admin.py — Admin-only routes for user management
Add to backend/app/api/ and register in main.py
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel

from app.db import get_db
from app.models import User
from app.schemas import UserOut
from app.api.auth import get_current_user

router = APIRouter()


def require_admin(user=Depends(get_current_user)):
    if not getattr(user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Admin required")
    return user


class RoleUpdate(BaseModel):
    role: str


class ActiveUpdate(BaseModel):
    is_active: bool


@router.get("/users", response_model=List[UserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    user=Depends(require_admin)
):
    result = await db.execute(select(User).order_by(User.created_at))
    return result.scalars().all()


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    body: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin)
):
    if body.role not in ("User", "Owner"):
        raise HTTPException(status_code=400, detail="Role must be 'User' or 'Owner'")
    result = await db.execute(select(User).where(User.id == user_id))
    u = result.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    if u.is_admin:
        raise HTTPException(status_code=400, detail="Cannot change admin role")
    u.role = body.role
    await db.commit()
    return {"detail": f"Role updated to {body.role}"}


@router.patch("/users/{user_id}/active")
async def toggle_user_active(
    user_id: int,
    body: ActiveUpdate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin)
):
    result = await db.execute(select(User).where(User.id == user_id))
    u = result.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    if u.is_admin:
        raise HTTPException(status_code=400, detail="Cannot deactivate admin")
    u.is_active = body.is_active
    await db.commit()
    return {"detail": "User updated"}



@router.post("/demo/reset")
async def reset_demo_data(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin)
):
    """
    Reset demo data - removes all reviews, orders, products, and cart items.
    Preserves user accounts for quick demo restart.
    """
    from app.models import Review, Order, OrderItem, Product, CartItem
    
    try:
        # Delete in order respecting foreign keys
        await db.execute("DELETE FROM orderitem")
        await db.execute("DELETE FROM \"order\"")
        await db.execute("DELETE FROM cartitem")
        await db.execute("DELETE FROM review")
        await db.execute("DELETE FROM product")
        await db.commit()
        
        return {
            "detail": "Demo data reset successfully",
            "message": "All products, reviews, orders, and cart items have been removed. User accounts preserved.",
            "next_step": "Run seed script to recreate demo data: python scripts/seed_demo_data.py"
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to reset demo data: {str(e)}")
