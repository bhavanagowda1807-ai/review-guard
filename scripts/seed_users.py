"""
seed_users.py — Creates 5 customers and 3 owners with realistic review history
so the metadata classifier has real account data to compute features from.

Run inside the backend container:
  docker compose exec backend python /app/scripts/seed_users.py
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import random

sys.path.insert(0, '/app')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from passlib.context import CryptContext

from app.models import User, Product, Order, OrderItem, Review

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db:5432/fake_review_db")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

OWNERS = [
    {"username": "techstore_owner", "full_name": "Arjun Mehta",  "email": "arjun@techstore.in",  "password": "owner@123"},
    {"username": "fashion_owner",   "full_name": "Priya Sharma", "email": "priya@fashionhub.in", "password": "owner@123"},
    {"username": "grocery_owner",   "full_name": "Ravi Kumar",   "email": "ravi@freshmart.in",   "password": "owner@123"},
]

USERS = [
    {"username": "Bhavana",        "full_name": "Bhavana S",    "email": "bhavana@gmail.com",  "password": "user@123", "account_age_days": 320, "review_count": 12, "avg_rating": 4.2, "profile": "genuine"},
    {"username": "rahul_shopper",  "full_name": "Rahul Verma",  "email": "rahul@gmail.com",    "password": "user@123", "account_age_days": 180, "review_count": 6,  "avg_rating": 3.8, "profile": "genuine"},
    {"username": "sneha_buys",     "full_name": "Sneha Rao",    "email": "sneha@gmail.com",    "password": "user@123", "account_age_days": 90,  "review_count": 4,  "avg_rating": 4.0, "profile": "genuine"},
    {"username": "fake_reviewer99","full_name": "Bot User",     "email": "bot99@spam.com",     "password": "user@123", "account_age_days": 5,   "review_count": 30, "avg_rating": 5.0, "profile": "fake"},
    {"username": "spammer_xyz",    "full_name": "Spammer X",    "email": "spamx@fake.com",     "password": "user@123", "account_age_days": 2,   "review_count": 50, "avg_rating": 5.0, "profile": "fake"},
]

GENUINE_REVIEWS = [
    ("Great product, exactly as described. Fast delivery!", 5),
    ("Good quality but a bit expensive for what it is.", 4),
    ("Works perfectly. Bought a second one for my sister.", 5),
    ("Decent product overall. Packaging could be better.", 3),
    ("Highly recommend! Used it daily for over two weeks.", 5),
    ("Not bad. Does what it says, no more no less.", 3),
    ("Really happy with this purchase. Very satisfied.", 4),
    ("Quality is excellent. Will definitely buy again.", 5),
    ("Arrived on time, product is exactly as expected.", 4),
    ("Good value for money. Satisfied with the purchase.", 4),
    ("Nice product but took longer than expected to arrive.", 3),
    ("Love it! Using it every single day now.", 5),
]

FAKE_REVIEWS = [
    ("BEST PRODUCT EVER!!! LOVE LOVE LOVE BUY NOW!!!", 5),
    ("Amazing amazing amazing. 10/10 perfect no issues.", 5),
    ("Wow this changed my life completely. Outstanding product!", 5),
    ("Perfect product. Everyone must buy this product today!!!", 5),
    ("Superb quality. Very nice. Much wow. Great value great.", 5),
    ("Excellent!!! Best purchase of my entire life I love it!!!", 5),
    ("This is the most wonderful thing I ever bought in life.", 5),
]


async def get_or_create_user(session, data, role="User"):
    result = await session.execute(select(User).where(User.username == data["username"]))
    existing = result.scalar_one_or_none()
    if existing:
        print(f"  ✓ {role} '{data['username']}' already exists, skipping.")
        return existing

    joined_at = datetime.utcnow() - timedelta(days=data.get("account_age_days", 100))
    user = User(
        username=data["username"],
        full_name=data.get("full_name", ""),
        email=data.get("email", ""),
        hashed_password=pwd.hash(data["password"]),
        role=role,
        is_admin=False,
        created_at=joined_at,
    )
    session.add(user)
    await session.flush()
    print(f"  ✓ Created {role}: {data['username']} (id={user.id})")
    return user


async def seed_reviews(session, user, user_data, products):
    if not products:
        return
    profile = user_data["profile"]
    review_count = user_data["review_count"]
    texts = GENUINE_REVIEWS if profile == "genuine" else FAKE_REVIEWS

    seeded = 0
    for i in range(review_count):
        product = products[i % len(products)]
        text, rating = texts[i % len(texts)]

        existing = await session.execute(
            select(Review).where(Review.user_id == user.id, Review.product_id == product.id)
        )
        if existing.scalar_one_or_none():
            continue

        # Spread reviews across time realistically
        days_ago = random.randint(1, user_data["account_age_days"])
        created = datetime.utcnow() - timedelta(days=days_ago)

        review = Review(
            user_id=user.id,
            product_id=product.id,
            text=text,
            rating=rating,
            verdict="genuine" if profile == "genuine" else "fake",
            confidence=0.85 if profile == "genuine" else 0.90,
            genuine_probability=0.85 if profile == "genuine" else 0.10,
            created_at=created,
        )
        session.add(review)
        seeded += 1

    await session.flush()
    print(f"    → Seeded {seeded} reviews for {user.username} ({profile} profile)")


async def main():
    print("\n🌱 Seeding users and review data...\n")

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Product))
        products = result.scalars().all()
        if not products:
            print("⚠️  No products found in shop. Users will be created but reviews skipped.")
            print("    Add products via Owner portal then re-run this script.\n")

        print("── Creating Owners ───────────────────────────────")
        for o in OWNERS:
            await get_or_create_user(session, o, role="Owner")

        print("\n── Creating Customers ────────────────────────────")
        for u_data in USERS:
            user = await get_or_create_user(session, u_data, role="User")
            if products:
                await seed_reviews(session, user, u_data, products)

        await session.commit()

    print("\n✅ Seeding complete!")
    print("\n── Login Credentials ─────────────────────────────")
    print("Customers (password: user@123):")
    for u in USERS:
        tag = "✅ genuine" if u["profile"] == "genuine" else "🚨 fake/bot"
        print(f"  {u['username']:<22} {tag}  (account age: {u['account_age_days']}d, reviews: {u['review_count']})")
    print("\nOwners (password: owner@123):")
    for o in OWNERS:
        print(f"  {o['username']}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
