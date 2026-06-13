from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import UserCreate, UserOut
from app.models import User
from app.db import get_db
from app.utils.password import get_password_hash, verify_password
from app.utils.jwt import create_access_token, decode_access_token
from app.core.config import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str = "User"  # "User", "Owner", "Admin"


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Invalid token")
    result = await db.execute(select(User).where(User.id == int(payload["sub"])))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def get_optional_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        return None
    result = await db.execute(select(User).where(User.id == int(payload["sub"])))
    return result.scalar_one_or_none()


async def require_shop_user(user: User = Depends(get_current_user)):
    """Allows only non-admin shop users. Admins must use ReviewGuard."""
    if getattr(user, "is_admin", False):
        raise HTTPException(
            status_code=403,
            detail="Admin accounts cannot access the shop. Please use the ReviewGuard portal.",
        )
    return user


async def require_owner_user(user: User = Depends(get_current_user)):
    """Allows Owner role or Admin. Regular shop users are blocked."""
    if not (getattr(user, "is_admin", False) or getattr(user, "role", "") in ["Admin", "Owner"]):
        raise HTTPException(status_code=403, detail="Seller account required.")
    return user


async def require_admin_user(user: User = Depends(get_current_user)):
    """Allows only admin users."""
    if not getattr(user, "is_admin", False):
        raise HTTPException(
            status_code=403,
            detail="Access denied. ReviewGuard is restricted to administrators only.",
        )
    return user

@router.post('/register', response_model=UserOut)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user.username))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail='Username already exists')

    result = await db.execute(select(User).limit(1))
    first_user = result.scalar_one_or_none() is None
    is_admin = False
    if first_user:
        if settings.INITIAL_ADMIN_USERNAME and user.username == settings.INITIAL_ADMIN_USERNAME:
            is_admin = True
        elif not settings.INITIAL_ADMIN_USERNAME:
            is_admin = True

    db_user = User(
        username=user.username,
        hashed_password=get_password_hash(user.password),
        is_admin=is_admin,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@router.post('/login', response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail='Incorrect username or password')
    access_token = create_access_token(subject=str(user.id))
    return {"access_token": access_token, "token_type": "bearer"}


@router.get('/me', response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user
