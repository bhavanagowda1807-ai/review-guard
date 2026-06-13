# 🚀 Quick Start - ReviewGuard Demo

Run ONE command to start everything!

## Windows

Double-click `start.bat` or run:
```bash
start.bat
```

## Linux / Mac

```bash
chmod +x start.sh
./start.sh
```

## What Happens Automatically

✅ Starts all Docker containers (Frontend, Backend, ML, DB)
✅ Configures CORS and static file serving
✅ Trains ML models
✅ **Seeds demo data automatically**:
   - 5 demo user accounts
   - 12 realistic products
   - 60+ mixed reviews (genuine + fake)
   - Sample orders

## Access the Demo

🌐 **Browser opens automatically to:** http://localhost:3000

### Demo Accounts (Password: `demo123`)

- **Admin**: admin@demo.com
- **Owner**: owner@demo.com
- **Customer**: customer@demo.com

## Two Platforms

1. **ReviewGuard** 🛡️ - Main Product
   - AI-powered detection console
   - Analytics dashboard
   - Bulk review upload
   - Admin access required

2. **ShopTrust** 🛒 - Live Demo
   - Interactive marketplace
   - Real-time AI verification
   - Color-coded reviews
   - Trust score indicators

## Demo Features

✨ **Visual Enhancements**
- Color-coded reviews (green/yellow/red)
- Real-time detection animations
- Trust score badges
- AI verification statistics

📦 **Pre-loaded Demo Data**
- Realistic product catalog
- Mixed review patterns showing AI detection
- Complete customer journeys
- Purchase history

## Troubleshooting

**Issue**: Demo data not showing
```bash
docker compose exec backend python /app/scripts/seed_demo_data.py
```

**Issue**: Need fresh demo for presentation
```bash
docker compose exec backend python /app/scripts/seed_demo_data.py reset
docker compose exec backend python /app/scripts/seed_demo_data.py
```

**Issue**: Services not starting
```bash
docker compose down
docker compose up -d --build
```

## Next Steps

1. ✅ Wait for startup to complete (2-3 minutes)
2. ✅ Browser opens automatically
3. ✅ Login with demo credentials
4. ✅ Explore ShopTrust marketplace
5. ✅ Write a review and watch AI analyze it
6. ✅ Switch to ReviewGuard admin console

## Documentation

📖 Full setup guide: `DEMO_SETUP_GUIDE.md`
🔑 All credentials: `DEMO_CREDENTIALS.md`
📋 Main README: `README.md`

---

**Ready to showcase in under 3 minutes!** 🎉
