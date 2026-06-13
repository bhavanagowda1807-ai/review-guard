"""Seed demo data for ReviewGuard demo with metadata for explanations."""
import asyncio
import json
import random
from sqlalchemy import select
from app.db import AsyncSessionLocal
from app.models import User, Product, Review
from app.utils.password import get_password_hash
from datetime import datetime, timedelta

DEMO_USERS = [
    {"username": "admin", "email": "admin@demo.com", "password": "adminpass", "is_admin": True},
    {"username": "owner", "email": "owner@demo.com", "password": "demo123", "is_admin": False},
    {"username": "customer", "email": "customer@demo.com", "password": "demo123", "is_admin": False},
    {"username": "alice", "email": "alice@demo.com", "password": "demo123", "is_admin": False},
    {"username": "bob", "email": "bob@demo.com", "password": "demo123", "is_admin": False},
]

DEMO_PRODUCTS = [
    {
        "name": "Premium Wireless Headphones",
        "category": "Electronics",
        "price": 2999.00,
        "description": "High-quality wireless headphones with noise cancellation and 30-hour battery life.",
        "keywords": "headphones, audio, wireless, noise-cancelling",
        "image_filename": "headphones.jpg",
    },
    {
        "name": "Yoga Mat Pro",
        "category": "Sports",
        "price": 899.00,
        "description": "Non-slip yoga mat with extra cushioning for comfort and stability.",
        "keywords": "yoga, fitness, mat, exercise",
        "image_filename": "yoga_mat.jpg",
    },
    {
        "name": "Organic Green Tea",
        "category": "Food",
        "price": 399.00,
        "description": "Premium organic green tea blend from the hills. Rich antioxidants.",
        "keywords": "tea, organic, green, health",
        "image_filename": "green_tea.jpg",
    },
    {
        "name": "Python Programming Book",
        "category": "Books",
        "price": 599.00,
        "description": "Complete guide to Python programming with real-world examples.",
        "keywords": "python, programming, book, coding",
        "image_filename": "python_book.jpg",
    },
    {
        "name": "Stainless Steel Water Bottle",
        "category": "Sports",
        "price": 499.00,
        "description": "Eco-friendly water bottle keeps drinks cold for 24 hours.",
        "keywords": "bottle, water, eco-friendly, sports",
        "image_filename": "water_bottle.jpg",
    },
    {
        "name": "Portable Phone Charger",
        "category": "Electronics",
        "price": 1299.00,
        "description": "20000mAh power bank with fast charging support.",
        "keywords": "charger, power bank, mobile, battery",
        "image_filename": "power_bank.jpg",
    },
    {
        "name": "Coffee Maker Deluxe",
        "category": "Kitchen",
        "price": 3499.00,
        "description": "Programmable coffee maker with thermal carafe.",
        "keywords": "coffee, maker, kitchen, appliance",
        "image_filename": "coffee_maker.jpg",
    },
    {
        "name": "Smartwatch Pro",
        "category": "Electronics",
        "price": 4999.00,
        "description": "Advanced smartwatch with health monitoring and GPS.",
        "keywords": "watch, smart, fitness, health",
        "image_filename": "smartwatch.jpg",
    },
    {
        "name": "Running Shoes Sport",
        "category": "Sports",
        "price": 2499.00,
        "description": "Professional running shoes with cushioned sole.",
        "keywords": "shoes, running, sports, comfort",
        "image_filename": "running_shoes.jpg",
    },
    {
        "name": "Organic Coffee Beans",
        "category": "Food",
        "price": 699.00,
        "description": "Premium organic coffee beans from Ethiopian highlands.",
        "keywords": "coffee, organic, beans, premium",
        "image_filename": "coffee_beans.jpg",
    },
    {
        "name": "JavaScript Guide",
        "category": "Books",
        "price": 549.00,
        "description": "Modern JavaScript development guide with ES6+ features.",
        "keywords": "javascript, programming, web, coding",
        "image_filename": "js_guide.jpg",
    },
    {
        "name": "LED Desk Lamp",
        "category": "Electronics",
        "price": 1199.00,
        "description": "Adjustable LED desk lamp with USB charging port.",
        "keywords": "lamp, led, desk, lighting",
        "image_filename": "desk_lamp.jpg",
    },
]

# Genuine reviews
GENUINE_REVIEWS = [
    {"text": "Great product! Been using it for 2 weeks now. Build quality is solid and works as advertised.", "rating": 5},
    {"text": "Really happy with this purchase. Exactly what I needed. Arrived on time too.", "rating": 5},
    {"text": "Good value for money. Works well but the packaging could be better.", "rating": 4},
    {"text": "Decent product. Not perfect but does the job. Would recommend to friends.", "rating": 4},
    {"text": "Excellent quality! Much better than other brands I've tried.", "rating": 5},
    {"text": "Very impressed with the quality and customer service. Will buy again!", "rating": 5},
    {"text": "It's okay. Works as expected. Nothing special but reliable.", "rating": 3},
    {"text": "Good product with minor flaws. Still worth the price.", "rating": 4},
    {"text": "Fantastic! Exceeded my expectations. Highly recommended.", "rating": 5},
    {"text": "Average product. Does what it's supposed to do.", "rating": 3},
    {"text": "Love it! Best purchase I've made in months.", "rating": 5},
    {"text": "Pretty good quality for the price. No complaints.", "rating": 4},
    {"text": "Solid product. Worth every penny spent.", "rating": 4},
    {"text": "Impressed with the durability. Looks like it'll last long.", "rating": 5},
    {"text": "Good quality but slightly overpriced in my opinion.", "rating": 3},
]

# Fake reviews
FAKE_REVIEWS = [
    {"text": "AMAZING!!! Best ever!!! Everyone should buy!!!! 10/10!!!", "rating": 5},
    {"text": "Simply perfect!!!!! No flaws whatsoever!!!!! Must buy!!!!", "rating": 5},
    {"text": "Incredible product!!!! Changed my life completely!!!! Wow!!", "rating": 5},
    {"text": "OMG this is literally the best thing ever!!!! So good!!!!", "rating": 5},
    {"text": "Fantastic fantastic fantastic!!!! 100% recommend!!!!", "rating": 5},
    {"text": "BEST PRODUCT EVER MADE!!!! LITERALLY PERFECT!!!!", "rating": 5},
    {"text": "you wont regret buying this its amazing trust me", "rating": 5},
    {"text": "better than all competitors combined 100%", "rating": 5},
    {"text": "Professional reviewer here. This product is revolutionary.", "rating": 5},
    {"text": "I gave this to my friend and family loves it too", "rating": 5},
    {"text": "totally worth it no questions asked seriously", "rating": 5},
    {"text": "this product saved my life literally", "rating": 5},
    {"text": "cant stop thinking about how amazing this is", "rating": 5},
    {"text": "all my friends want one now after seeing mine", "rating": 5},
    {"text": "wish i had bought this sooner would have saved me so much time", "rating": 5},
]


def _make_genuine_reasoning(confidence: float, genuine_prob: float, metadata: dict) -> str:
    """Create reasoning for genuine reviews with full metadata."""
    return json.dumps({
        "verdict": "genuine",
        "confidence": round(confidence, 4),
        "genuine_probability": round(genuine_prob, 4),
        "fusion_strategy": "attention",
        "modal_scores": {
            "text_score": round(random.uniform(0.05, 0.30), 4),
            "metadata_score": round(random.uniform(0.05, 0.25), 4),
        },
        "attention_weights": {"text": 0.6, "metadata": 0.4},
        "linguistic": {
            "superlative_count": random.randint(0, 1),
            "readability": round(random.uniform(45.0, 75.0), 1),
            "sentence_variance": round(random.uniform(0.5, 4.0), 1),
            "pronoun_ratio": round(random.uniform(0.05, 0.15), 2),
            "sentiment_mismatch": round(random.uniform(0.0, 0.08), 2),
        },
        "top_meta_signals": [
            {"feature": "Account Age (days)", "value": metadata.get("account_age", 180)},
            {"feature": "Reviews Per Day", "value": round(metadata.get("reviews_per_day", 0.5), 4)},
            {"feature": "Verified Purchase Ratio", "value": round(metadata.get("verified_purchase_ratio", 0.8), 4)},
            {"feature": "Rating Deviation", "value": round(metadata.get("rating_deviation", 0.3), 4)},
            {"feature": "Similarity Score", "value": round(random.uniform(0.0, 0.2), 4)},
            {"feature": "Reviewer Overlap", "value": round(random.uniform(0.0, 0.15), 4)},
            {"feature": "Helpfulness Ratio", "value": round(metadata.get("helpfulness_ratio", 0.7), 4)},
        ],
    })


def _make_fake_reasoning(confidence: float, genuine_prob: float, metadata: dict) -> str:
    """Create reasoning for fake reviews with full metadata."""
    return json.dumps({
        "verdict": "fake",
        "confidence": round(confidence, 4),
        "genuine_probability": round(genuine_prob, 4),
        "fusion_strategy": "attention",
        "modal_scores": {
            "text_score": round(random.uniform(0.65, 0.95), 4),
            "metadata_score": round(random.uniform(0.70, 0.98), 4),
        },
        "attention_weights": {"text": 0.55, "metadata": 0.45},
        "linguistic": {
            "superlative_count": random.randint(2, 5),
            "readability": round(random.uniform(15.0, 45.0), 1),
            "sentence_variance": round(random.uniform(6.0, 18.0), 1),
            "pronoun_ratio": round(random.uniform(0.20, 0.55), 2),
            "sentiment_mismatch": round(random.uniform(0.25, 0.85), 2),
        },
        "top_meta_signals": [
            {"feature": "Account Age (days)", "value": metadata.get("account_age", 7)},
            {"feature": "Reviews Per Day", "value": round(metadata.get("reviews_per_day", 3.5), 4)},
            {"feature": "Verified Purchase Ratio", "value": round(metadata.get("verified_purchase_ratio", 0.1), 4)},
            {"feature": "Rating Deviation", "value": round(metadata.get("rating_deviation", 1.8), 4)},
            {"feature": "Burstiness", "value": round(metadata.get("burstiness", 6.5), 4)},
            {"feature": "Sentiment Rating Mismatch", "value": round(metadata.get("sentiment_rating_mismatch", 0.7), 4)},
            {"feature": "Similarity Score", "value": round(random.uniform(0.6, 0.98), 4)},
            {"feature": "Reviewer Overlap", "value": round(random.uniform(0.5, 0.95), 4)},
        ],
    })


# User metadata profiles - matching each user's characteristics
USER_METADATA = {
    "customer": {
        "genuine": {
            "account_age": random.randint(180, 720),
            "reviews_per_day": round(random.uniform(0.3, 0.8), 2),
            "verified_purchase_ratio": round(random.uniform(0.7, 0.95), 2),
            "rating_deviation": round(random.uniform(0.2, 0.5), 2),
            "burstiness": round(random.uniform(0.5, 1.5), 2),
            "helpfulness_ratio": round(random.uniform(0.6, 0.85), 2),
            "night_review_ratio": round(random.uniform(0.1, 0.3), 2),
        },
        "fake": {
            "account_age": random.randint(1, 30),
            "reviews_per_day": round(random.uniform(2.0, 5.0), 2),
            "verified_purchase_ratio": round(random.uniform(0.0, 0.2), 2),
            "rating_deviation": round(random.uniform(1.5, 2.5), 2),
            "burstiness": round(random.uniform(4.0, 8.0), 2),
            "helpfulness_ratio": round(random.uniform(0.1, 0.3), 2),
            "night_review_ratio": round(random.uniform(0.5, 0.9), 2),
        }
    },
    "alice": {
        "genuine": {
            "account_age": random.randint(200, 800),
            "reviews_per_day": round(random.uniform(0.4, 1.0), 2),
            "verified_purchase_ratio": round(random.uniform(0.75, 0.98), 2),
            "rating_deviation": round(random.uniform(0.15, 0.4), 2),
            "burstiness": round(random.uniform(0.3, 1.2), 2),
            "helpfulness_ratio": round(random.uniform(0.65, 0.90), 2),
            "night_review_ratio": round(random.uniform(0.05, 0.2), 2),
        },
        "fake": {
            "account_age": random.randint(2, 20),
            "reviews_per_day": round(random.uniform(3.0, 6.0), 2),
            "verified_purchase_ratio": round(random.uniform(0.0, 0.15), 2),
            "rating_deviation": round(random.uniform(1.8, 2.5), 2),
            "burstiness": round(random.uniform(5.0, 9.0), 2),
            "helpfulness_ratio": round(random.uniform(0.05, 0.25), 2),
            "night_review_ratio": round(random.uniform(0.6, 0.95), 2),
        }
    },
    "bob": {
        "genuine": {
            "account_age": random.randint(150, 600),
            "reviews_per_day": round(random.uniform(0.25, 0.6), 2),
            "verified_purchase_ratio": round(random.uniform(0.65, 0.92), 2),
            "rating_deviation": round(random.uniform(0.25, 0.6), 2),
            "burstiness": round(random.uniform(0.6, 1.8), 2),
            "helpfulness_ratio": round(random.uniform(0.55, 0.80), 2),
            "night_review_ratio": round(random.uniform(0.15, 0.35), 2),
        },
        "fake": {
            "account_age": random.randint(3, 25),
            "reviews_per_day": round(random.uniform(2.5, 4.5), 2),
            "verified_purchase_ratio": round(random.uniform(0.0, 0.25), 2),
            "rating_deviation": round(random.uniform(1.6, 2.4), 2),
            "burstiness": round(random.uniform(3.5, 7.5), 2),
            "helpfulness_ratio": round(random.uniform(0.08, 0.35), 2),
            "night_review_ratio": round(random.uniform(0.55, 0.90), 2),
        }
    },
    "owner": {
        "genuine": {
            "account_age": random.randint(365, 1095),
            "reviews_per_day": round(random.uniform(0.1, 0.4), 2),
            "verified_purchase_ratio": round(random.uniform(0.80, 0.99), 2),
            "rating_deviation": round(random.uniform(0.1, 0.3), 2),
            "burstiness": round(random.uniform(0.2, 0.8), 2),
            "helpfulness_ratio": round(random.uniform(0.70, 0.95), 2),
            "night_review_ratio": round(random.uniform(0.05, 0.15), 2),
        },
        "fake": {
            "account_age": random.randint(5, 35),
            "reviews_per_day": round(random.uniform(1.5, 3.5), 2),
            "verified_purchase_ratio": round(random.uniform(0.0, 0.3), 2),
            "rating_deviation": round(random.uniform(1.7, 2.5), 2),
            "burstiness": round(random.uniform(4.5, 8.5), 2),
            "helpfulness_ratio": round(random.uniform(0.10, 0.40), 2),
            "night_review_ratio": round(random.uniform(0.50, 0.95), 2),
        }
    },
}


async def seed_demo_data():
    """Seed demo data into the database with metadata."""
    async with AsyncSessionLocal() as session:
        print("🌱 Starting demo data seed with metadata...")

        # Create users
        print("\n👥 Creating demo users...")
        for user_data in DEMO_USERS:
            result = await session.execute(
                select(User).where(User.username == user_data["username"])
            )
            existing = result.scalar_one_or_none()
            if not existing:
                user = User(
                    username=user_data["username"],
                    hashed_password=get_password_hash(user_data["password"]),
                    is_admin=user_data.get("is_admin", False),
                )
                session.add(user)
                print(f"  ✅ Created user: {user_data['username']}")
            else:
                print(f"  ⏭️  User already exists: {user_data['username']}")

        await session.commit()

        # Create products
        print("\n🛍️  Creating demo products...")
        products = []
        for idx, prod_data in enumerate(DEMO_PRODUCTS, 1):
            result = await session.execute(
                select(Product).where(Product.name == prod_data["name"])
            )
            existing = result.scalar_one_or_none()
            if not existing:
                admin_result = await session.execute(
                    select(User).where(User.username == "admin")
                )
                admin = admin_result.scalar_one_or_none()

                product = Product(
                    name=prod_data["name"],
                    category=prod_data["category"],
                    price=prod_data["price"],
                    description=prod_data["description"],
                    keywords=prod_data["keywords"],
                    image_filename=prod_data["image_filename"],
                    added_by=admin.id if admin else 1,
                    is_active=True,
                )
                session.add(product)
                products.append(product)
                print(f"  ✅ Created product: {prod_data['name']}")
            else:
                print(f"  ⏭️  Product already exists: {prod_data['name']}")

        await session.commit()

        # Refresh products to get their IDs
        for product in products:
            await session.refresh(product)

        # Create reviews
        print("\n⭐ Creating demo reviews with metadata...")
        product_result = await session.execute(select(Product))
        all_products = product_result.scalars().all()

        user_result = await session.execute(select(User).where(User.username != "admin"))
        all_users = user_result.scalars().all()
        user_map = {u.username: u for u in all_users}

        review_count = 0
        for product in all_products:
            num_reviews = random.randint(5, 8)
            num_genuine = int(num_reviews * 0.7)
            num_fake = num_reviews - num_genuine

            # Add genuine reviews
            for _ in range(num_genuine):
                review_data = random.choice(GENUINE_REVIEWS)
                user = random.choice(all_users)
                confidence = random.uniform(0.75, 0.99)
                genuine_prob = random.uniform(0.75, 0.99)
                
                # Get metadata for user
                user_meta = USER_METADATA.get(user.username, {}).get("genuine", {})
                if not user_meta:
                    user_meta = USER_METADATA["customer"]["genuine"]

                review = Review(
                    product_id=product.id,
                    user_id=user.id,
                    text=review_data["text"],
                    rating=review_data["rating"],
                    verdict="genuine",
                    confidence=confidence,
                    genuine_probability=genuine_prob,
                    reasoning=_make_genuine_reasoning(confidence, genuine_prob, user_meta),
                )
                session.add(review)
                review_count += 1

            # Add fake reviews
            for _ in range(num_fake):
                review_data = random.choice(FAKE_REVIEWS)
                user = random.choice(all_users)
                confidence = random.uniform(0.75, 0.99)
                genuine_prob = random.uniform(0.0, 0.25)
                
                # Get metadata for user
                user_meta = USER_METADATA.get(user.username, {}).get("fake", {})
                if not user_meta:
                    user_meta = USER_METADATA["customer"]["fake"]

                review = Review(
                    product_id=product.id,
                    user_id=user.id,
                    text=review_data["text"],
                    rating=review_data["rating"],
                    verdict="fake",
                    confidence=confidence,
                    genuine_probability=genuine_prob,
                    reasoning=_make_fake_reasoning(confidence, genuine_prob, user_meta),
                )
                session.add(review)
                review_count += 1

        await session.commit()
        print(f"  ✅ Created {review_count} reviews with metadata")

        print("\n✨ Demo data seeding complete!")
        print(f"  - {len(DEMO_USERS)} users")
        print(f"  - {len(all_products)} products")
        print(f"  - {review_count} reviews (with explanations)")
        print("\n🎉 Ready to demo! Access at http://localhost:3000")


async def main():
    await seed_demo_data()


if __name__ == "__main__":
    asyncio.run(main())
