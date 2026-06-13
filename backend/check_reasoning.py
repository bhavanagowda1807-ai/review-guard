import sys
sys.path.insert(0, '/app')
import asyncio
import json
from app.db import AsyncSessionLocal
from app.models import Review
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Review).limit(5))
        reviews = result.scalars().all()
        for r in reviews:
            if r.reasoning:
                try:
                    data = json.loads(r.reasoning)
                    print(f"Review {r.id}:")
                    print(f"  Keys: {list(data.keys())}")
                    if 'top_meta_signals' in data:
                        print(f"  Meta signals count: {len(data['top_meta_signals'])}")
                        if data['top_meta_signals']:
                            print(f"  First signal: {data['top_meta_signals'][0]}")
                except:
                    pass
                print()

asyncio.run(check())
