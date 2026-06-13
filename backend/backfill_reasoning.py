import asyncio
import sys
import os
import httpx
sys.path.insert(0, '/app')

from app.db import AsyncSessionLocal
from app.models import Review
from app.celery_worker import run_inference_task
from app.api.inference import _build_reasoning
from sqlalchemy import select
ML_URL = os.getenv("ML_SERVICE_URL", "http://ml_inference:8501").rstrip("/")
async def backfill():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Review).where(Review.reasoning == None).limit(200)
        )
        reviews = result.scalars().all()
        updated = 0
        async with httpx.AsyncClient(timeout=30) as client:
            for r in reviews:
                try:
                    data = {
                        "text": r.text or "",
                        "rating": str(r.rating or 3),
                        "fusion_strategy": "attention",
                    }
                    resp = await client.post(f"{ML_URL}/predict", data=data)
                    resp.raise_for_status()
                    ml = resp.json()
                    reasoning = _build_reasoning(ml)
                    if reasoning:
                        r.reasoning = reasoning
                        db.add(r)
                        await db.flush()
                        updated += 1
                except Exception as e:
                    print(f"  ✗ {e}")
                    continue
        await db.commit()
        print(f"Backfilled {updated} reviews")

if __name__ == '__main__':
    asyncio.run(backfill())
