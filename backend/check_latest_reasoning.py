import sys
sys.path.insert(0, '/app')
import asyncio
import json
from app.db import AsyncSessionLocal
from app.models import Review
from sqlalchemy import select, desc

async def check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Review).order_by(desc(Review.id)).limit(5))
        reviews = result.scalars().all()
        for r in reviews:
            print(f"Review {r.id} (created: {r.created_at}):")
            if r.reasoning:
                try:
                    data = json.loads(r.reasoning)
                    print(f"  Keys: {list(data.keys())}")
                    if 'top_meta_signals' in data:
                        print(f"  Meta signals count: {len(data['top_meta_signals'])}")
                        if data['top_meta_signals']:
                            for sig in data['top_meta_signals'][:3]:
                                print(f"    - {sig['feature']}: {sig['value']}")
                except Exception as e:
                    print(f"  Error: {e}")
            else:
                print(f"  No reasoning")
            print()

asyncio.run(check())
