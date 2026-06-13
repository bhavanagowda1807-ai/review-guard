from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from app.db import async_engine, AsyncSessionLocal
from sqlmodel import SQLModel
from app.models import User, Review
import mlflow
from app.core.config import settings
from app.utils.password import get_password_hash
from app.api.shop import router as shop_router
from app.api.admin import router as admin_router



app = FastAPI(title="Multimodal Fake Review Detection - Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "backend"}

@app.on_event("startup")
async def on_startup():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    if settings.INITIAL_ADMIN_USERNAME and settings.INITIAL_ADMIN_PASSWORD:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).limit(1))
            existing = result.scalar_one_or_none()
            if existing is None:
                admin = User(
                    username=settings.INITIAL_ADMIN_USERNAME,
                    hashed_password=get_password_hash(settings.INITIAL_ADMIN_PASSWORD),
                    is_admin=True,
                )
                session.add(admin)
                await session.commit()
                print(f'Created initial admin user: {settings.INITIAL_ADMIN_USERNAME}')

    try:
        if getattr(settings, 'MLFLOW_TRACKING_URI', None):
            mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
            mlflow.set_experiment('multimodal_fake_review_detection')
    except Exception:
        pass

from app.api import auth, inference  # noqa

app.include_router(auth.router, prefix="/auth")
app.include_router(inference.router, prefix="/api")
app.include_router(shop_router, prefix="/api/shop", tags=["shop"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
