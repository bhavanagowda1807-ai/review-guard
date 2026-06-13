# Demo Credentials for ReviewGuard System

## Demo Accounts

All demo accounts use the password: `demo123`

### ShopTrust (E-commerce Demo)

**Admin Account:**
- Email: `admin@demo.com`
- Password: `demo123`
- Role: Admin (Full access to ReviewGuard admin console)

**Shop Owner Account:**
- Email: `owner@demo.com`
- Password: `demo123`
- Role: Owner (Can manage products and view orders)

**Customer Accounts:**
- Email: `customer@demo.com` / Password: `demo123`
- Email: `alice@demo.com` / Password: `demo123`
- Email: `bob@demo.com` / Password: `demo123`
- Role: User (Can shop and write reviews)

### ReviewGuard (Admin Console)

Use the admin account to access the ReviewGuard admin console:
- Email: `admin@demo.com`
- Password: `demo123`

## How to Seed Demo Data

Run the seeding script to populate the database with demo products and reviews:

```bash
python scripts/seed_demo_data.py
```

To reset demo data (keeps users, removes products/reviews):

```bash
python scripts/seed_demo_data.py reset
```

## What Gets Seeded

- **5 Demo Users**: Admin, Owner, and 3 customers
- **12 Products**: Across various categories (Electronics, Sports, Food, etc.)
- **Mixed Reviews**: ~70% genuine, ~30% fake (demonstrating AI detection)
- **Sample Orders**: Customer purchase history

## Demo Flow

1. **ShopTrust Experience**:
   - Login as customer
   - Browse products with AI-verified reviews
   - See trust scores and confidence ratings
   - Write reviews (get analyzed in real-time)

2. **ReviewGuard Console**:
   - Login as admin
   - View all detected reviews
   - See confidence scores and verdicts
   - Analyze fake review patterns
   - View analytics dashboard

## Notes

- All reviews are analyzed by the ML system
- Genuine reviews show green verification badges
- Fake reviews show red warning indicators
- Trust scores calculated based on genuine/fake ratio
