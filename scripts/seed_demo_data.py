#!/usr/bin/env python3
"""
Demo Data Seeding Script for ReviewGuard + ShopTrust
Creates realistic products, users, and reviews (genuine + fake patterns) for demonstration purposes
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
import random

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import async_engine, AsyncSessionLocal
from app.models import User, Product, Review, Order, OrderItem
from app.utils.password import get_password_hash
from sqlmodel import SQLModel


# Demo Accounts
DEMO_USERS = [
    {
        "username": "admin",
        "email": "admin@demo.com",
        "password": "demo123",
        "full_name": "Admin User",
        "is_admin": True,
        "role": "Admin"
    },
    {
        "username": "owner",
        "email": "owner@demo.com",
        "password": "demo123",
        "full_name": "Shop Owner",
        "is_admin": False,
        "role": "Owner"
    },
    {
        "username": "customer",
        "email": "customer@demo.com",
        "password": "demo123",
        "full_name": "Regular Customer",
        "is_admin": False,
        "role": "User"
    },
    {
        "username": "alice",
        "email": "alice@demo.com",
        "password": "demo123",
        "full_name": "Alice Johnson",
        "is_admin": False,
        "role": "User"
    },
    {
        "username": "bob",
        "email": "bob@demo.com",
        "password": "demo123",
        "full_name": "Bob Smith",
        "is_admin": False,
        "role": "User"
    },
]

# Demo Products
DEMO_PRODUCTS = [
    {
        "name": "Premium Wireless Headphones",
        "category": "Electronics",
        "price": 4999,
        "description": "High-quality wireless headphones with noise cancellation and 30-hour battery life",
        "keywords": "wireless, bluetooth, noise cancelling, audio"
    },
    {
        "name": "Smart Fitness Watch",
        "category": "Electronics",
        "price": 3499,
        "description": "Track your fitness goals with heart rate monitoring, GPS, and sleep tracking",
        "keywords": "fitness, smartwatch, health, tracking"
    },
    {
        "name": "Organic Green Tea - 100g",
        "category": "Food",
        "price": 299,
        "description": "Premium organic green tea leaves from the Himalayan region",
        "keywords": "tea, organic, healthy, beverage"
    },
    {
        "name": "Yoga Mat Pro",
        "category": "Sports",
        "price": 1299,
        "description": "Extra thick, non-slip yoga mat perfect for all types of yoga and exercise",
        "keywords": "yoga, fitness, exercise, mat"
    },
    {
        "name": "Bestselling Mystery Novel",
        "category": "Books",
        "price": 399,
        "description": "A gripping thriller that will keep you on the edge of your seat",
        "keywords": "book, mystery, thriller, fiction"
    },
    {
        "name": "Leather Wallet",
        "category": "Fashion",
        "price": 899,
        "description": "Genuine leather wallet with RFID protection and multiple card slots",
        "keywords": "wallet, leather, accessories, fashion"
    },
    {
        "name": "Portable Bluetooth Speaker",
        "category": "Electronics",
        "price": 2499,
        "description": "Waterproof speaker with 360-degree sound and 20-hour battery",
        "keywords": "speaker, bluetooth, portable, audio"
    },
    {
        "name": "Stainless Steel Water Bottle",
        "category": "Home",
        "price": 599,
        "description": "Insulated water bottle keeps drinks cold for 24 hours or hot for 12 hours",
        "keywords": "bottle, water, insulated, eco-friendly"
    },
    {
        "name": "Gaming Mouse RGB",
        "category": "Electronics",
        "price": 1799,
        "description": "High-precision gaming mouse with customizable RGB lighting and programmable buttons",
        "keywords": "gaming, mouse, rgb, computer"
    },
    {
        "name": "Natural Face Serum",
        "category": "Beauty",
        "price": 1499,
        "description": "Vitamin C enriched face serum for glowing skin",
        "keywords": "skincare, serum, beauty, organic"
    },
    {
        "name": "Chef's Knife Set",
        "category": "Home",
        "price": 2999,
        "description": "Professional-grade stainless steel knife set with 5 essential knives",
        "keywords": "kitchen, knives, cooking, utensils"
    },
    {
        "name": "Running Shoes Pro",
        "category": "Sports",
        "price": 3999,
        "description": "Lightweight running shoes with superior cushioning and breathable mesh",
        "keywords": "shoes, running, sports, fitness"
    },
]

# Genuine Review Templates (natural, varied, specific details)
GENUINE_REVIEWS = [
    {
        "templates": [
            "I've been using this {product} for about {time} now and I'm really impressed. {detail}. Definitely worth the price!",
            "Bought this as a gift and the recipient loved it. {detail}. Would recommend to anyone looking for quality.",
            "Good value for money. {detail}. Only minor issue is {small_issue} but that's not a dealbreaker.",
            "Decent {category} product. {detail}. Does what it's supposed to do, no complaints so far.",
            "After comparing several options, I chose this one. {detail}. Happy with my purchase overall."
        ],
        "details": [
            "The build quality is solid and feels premium",
            "It works exactly as advertised",
            "The battery life is better than expected",
            "Very comfortable to use for long periods",
            "Easy to set up and use right out of the box",
            "The sound quality exceeded my expectations",
            "Great design and fits perfectly in my daily routine"
        ],
        "small_issues": [
            "the packaging could be better",
            "it took a few days to get used to",
            "the instructions could be clearer",
            "shipping took longer than expected"
        ],
        "times": ["2 weeks", "a month", "3 weeks", "about a week"]
    }
]

# Fake Review Templates (generic, overly enthusiastic, suspicious patterns)
FAKE_REVIEWS = [
    {
        "templates": [
            "Amazing product!!! Best purchase ever!!!! Highly recommend to everyone!!!!",
            "This is the BEST {category} I've ever bought! 5 stars! Perfect! Excellent!",
            "Wow, just wow! This product changed my life! Everyone should buy this now!",
            "Absolutely perfect in every way! No flaws at all! Buy immediately!",
            "Great great great! Very good! Excellent quality! Best price! Must buy!"
        ]
    }
]

# More nuanced fake patterns
SUSPICIOUS_REVIEWS = [
    {
        "templates": [
            "I received this product at a discount for my honest review. It's pretty good, 5 stars!",
            "The seller asked me to write a review. This is an excellent product, highly recommended!",
            "Got this for free to test. Amazing! Perfect! Best ever!",
        ]
    }
]


async def create_demo_users(session: AsyncSession):
    """Create demo user accounts"""
    print("📝 Creating demo users...")
    created_users = []
    
    for user_data in DEMO_USERS:
        # Check if user already exists
        result = await session.execute(
            select(User).where(User.email == user_data["email"])
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"  ✓ User {user_data['username']} already exists")
            created_users.append(existing)
            continue
        
        user = User(
            username=user_data["username"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            hashed_password=get_password_hash(user_data["password"]),
            is_admin=user_data["is_admin"],
            role=user_data["role"],
            created_at=datetime.utcnow() - timedelta(days=random.randint(30, 180))
        )
        session.add(user)
        created_users.append(user)
        print(f"  ✓ Created user: {user_data['username']} ({user_data['email']})")
    
    await session.commit()
    return created_users


async def create_demo_products(session: AsyncSession, owner_id: int):
    """Create demo products"""
    print("\n📦 Creating demo products...")
    created_products = []
    
    for product_data in DEMO_PRODUCTS:
        # Check if product already exists
        result = await session.execute(
            select(Product).where(Product.name == product_data["name"])
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"  ✓ Product '{product_data['name']}' already exists")
            created_products.append(existing)
            continue
        
        product = Product(
            name=product_data["name"],
            category=product_data["category"],
            price=product_data["price"],
            description=product_data["description"],
            keywords=product_data["keywords"],
            added_by=owner_id,
            is_active=True,
            created_at=datetime.utcnow() - timedelta(days=random.randint(10, 90))
        )
        session.add(product)
        created_products.append(product)
        print(f"  ✓ Created product: {product_data['name']} - ₹{product_data['price']}")
    
    await session.commit()
    return created_products


async def create_demo_reviews(session: AsyncSession, users: list, products: list):
    """Create a mix of genuine and fake reviews"""
    print("\n💬 Creating demo reviews...")
    
    # Regular customers (not admin/owner)
    regular_users = [u for u in users if u.role == "User"]
    
    review_count = 0
    genuine_count = 0
    fake_count = 0
    
    for product in products:
        # Each product gets 3-8 reviews
        num_reviews = random.randint(3, 8)
        
        # 70% genuine, 30% fake distribution
        num_genuine = int(num_reviews * 0.7)
        num_fake = num_reviews - num_genuine
        
        # Create genuine reviews
        for _ in range(num_genuine):
            user = random.choice(regular_users)
            template = random.choice(GENUINE_REVIEWS[0]["templates"])
            detail = random.choice(GENUINE_REVIEWS[0]["details"])
            time_period = random.choice(GENUINE_REVIEWS[0]["times"])
            small_issue = random.choice(GENUINE_REVIEWS[0]["small_issues"])
            
            review_text = template.format(
                product=product.name,
                category=product.category.lower(),
                detail=detail,
                small_issue=small_issue,
                time=time_period
            )
            
            rating = random.choices([3, 4, 5], weights=[0.1, 0.3, 0.6])[0]
            
            review = Review(
                user_id=user.id,
                product_id=product.id,
                text=review_text,
                rating=rating,
                verdict="genuine",
                confidence=random.uniform(0.75, 0.95),
                genuine_probability=random.uniform(0.75, 0.95),
                fusion_strategy="attention",
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 60))
            )
            session.add(review)
            genuine_count += 1
        
        # Create fake reviews
        for _ in range(num_fake):
            user = random.choice(regular_users)
            
            # Mix of obvious fake and suspicious patterns
            if random.random() < 0.6:
                template = random.choice(FAKE_REVIEWS[0]["templates"])
                review_text = template.format(category=product.category.lower())
            else:
                review_text = random.choice(SUSPICIOUS_REVIEWS[0]["templates"])
            
            rating = 5  # Fake reviews typically give 5 stars
            
            review = Review(
                user_id=user.id,
                product_id=product.id,
                text=review_text,
                rating=rating,
                verdict="fake",
                confidence=random.uniform(0.70, 0.92),
                genuine_probability=random.uniform(0.05, 0.30),
                fusion_strategy="attention",
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                flagged=random.random() < 0.3  # 30% of fake reviews are flagged
            )
            session.add(review)
            fake_count += 1
        
        review_count += num_reviews
    
    await session.commit()
    print(f"  ✓ Created {review_count} reviews")
    print(f"    - {genuine_count} genuine reviews (AI verified)")
    print(f"    - {fake_count} fake reviews (AI flagged)")


async def create_demo_orders(session: AsyncSession, users: list, products: list):
    """Create some sample orders"""
    print("\n🛒 Creating demo orders...")
    
    regular_users = [u for u in users if u.role == "User"]
    order_count = 0
    
    for user in regular_users[:3]:  # Create orders for first 3 customers
        # Each customer has 1-3 orders
        num_orders = random.randint(1, 3)
        
        for _ in range(num_orders):
            # Pick 1-3 products per order
            order_products = random.sample(products, random.randint(1, 3))
            total_amount = sum(p.price for p in order_products)
            
            order = Order(
                user_id=user.id,
                total_amount=total_amount,
                payment_method=random.choice(["card", "upi", "wallet"]),
                status=random.choice(["completed", "Delivered"]),
                ordered_at=datetime.utcnow() - timedelta(days=random.randint(5, 45))
            )
            session.add(order)
            await session.flush()
            
            for product in order_products:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=1,
                    price_at_purchase=product.price
                )
                session.add(order_item)
            
            order_count += 1
    
    await session.commit()
    print(f"  ✓ Created {order_count} demo orders")


async def seed_demo_data():
    """Main seeding function"""
    print("🌱 Starting demo data seeding...\n")
    print("=" * 60)
    
    # Create tables
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    async with AsyncSessionLocal() as session:
        # Create users
        users = await create_demo_users(session)
        
        # Get owner user for product creation
        owner = next((u for u in users if u.role == "Owner"), users[0])
        
        # Create products
        products = await create_demo_products(session, owner.id)
        
        # Create reviews
        await create_demo_reviews(session, users, products)
        
        # Create orders
        await create_demo_orders(session, users, products)
    
    print("\n" + "=" * 60)
    print("✅ Demo data seeding completed successfully!\n")
    print("🔑 Demo Account Credentials:")
    print("   Admin:    admin@demo.com / demo123")
    print("   Owner:    owner@demo.com / demo123")
    print("   Customer: customer@demo.com / demo123")
    print("\n💡 Access the application:")
    print("   - ShopTrust:   http://localhost:3000/shoptrust/login")
    print("   - ReviewGuard: http://localhost:3000/reviewguard/login")
    print("=" * 60)


async def reset_demo_data():
    """Reset demo data - removes all reviews, orders, products"""
    print("🔄 Resetting demo data...\n")
    
    async with AsyncSessionLocal() as session:
        # Delete in correct order (respecting foreign keys)
        await session.execute("DELETE FROM orderitem")
        await session.execute("DELETE FROM \"order\"")
        await session.execute("DELETE FROM review")
        await session.execute("DELETE FROM product")
        await session.execute("DELETE FROM cartitem")
        await session.commit()
        
        print("✅ Demo data reset complete. Users preserved.")
        print("   Run with 'seed' command to recreate demo data.")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "seed"
    
    if command == "reset":
        asyncio.run(reset_demo_data())
    else:
        asyncio.run(seed_demo_data())
