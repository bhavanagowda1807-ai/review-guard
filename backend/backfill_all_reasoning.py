import asyncio
import sys
sys.path.insert(0, '/app')

from app.db import AsyncSessionLocal
from app.models import Review
from app.api.inference import _build_reasoning
from sqlalchemy import select, or_

async def backfill():
    async with AsyncSessionLocal() as db:
        # Get all reviews without reasoning or with empty reasoning
        result = await db.execute(
            select(Review).where(
                or_(Review.reasoning == None, Review.reasoning == '')
            )
        )
        reviews = result.scalars().all()
        print(f"Found {len(reviews)} reviews to backfill")
        
        updated = 0
        for i, r in enumerate(reviews):
            try:
                # Create a minimal ML response from existing verdict data
                ml = {
                    "verdict": r.verdict or "pending",
                    "confidence": r.confidence or 0.5,
                    "genuine_probability": r.genuine_probability or 0.5,
                    "fusion_strategy": r.fusion_strategy or "attention",
                    "modal_scores": {},
                    "attention": {"text": 0.5, "metadata": 0.5},
                    "text_features": {},
                    "metadata_features": {},
                }
                
                reasoning = _build_reasoning(ml)
                if reasoning:
                    r.reasoning = reasoning
                    db.add(r)
                    updated += 1
                    if (i + 1) % 50 == 0:
                        print(f"  Processed {i+1}/{len(reviews)}...")
            except Exception as e:
                print(f"Error on review {r.id}: {e}")
                continue
        
        await db.commit()
        print(f"Backfilled reasoning for {updated}/{len(reviews)} reviews")

asyncio.run(backfill())
