# 🎬 ReviewGuard + ShopTrust Demo Setup Guide

This guide will help you set up and run the impressive demo showcase for ReviewGuard's fake review detection system.

## 🚀 Quick Start

### 1. Start the Application

```bash
docker-compose up --build
```

Wait for all services to start:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- ML Inference: http://localhost:8501
- MLflow: http://localhost:5000

### 2. Seed Demo Data

```bash
# Enter the backend container
docker-compose exec backend bash

# Run the seed script
python /app/scripts/seed_demo_data.py
```

This will create:
- ✅ 5 demo user accounts
- ✅ 12 realistic products across categories
- ✅ ~60 mixed reviews (70% genuine, 30% fake)
- ✅ Sample customer orders

### 3. Access the Demo

**Landing Page**: http://localhost:3000

Choose your experience:
- **ReviewGuard** 🛡️ - Admin console (Core product)
- **ShopTrust** 🛒 - Live demo marketplace

---

## 🔑 Demo Credentials

All accounts use password: `demo123`

| Role | Email | Access |
|------|-------|--------|
| **Admin** | admin@demo.com | Full ReviewGuard admin console |
| **Owner** | owner@demo.com | Shop management dashboard |
| **Customer** | customer@demo.com | Shopping and reviews |
| **Customer** | alice@demo.com | Shopping and reviews |
| **Customer** | bob@demo.com | Shopping and reviews |

---

## 🎯 Demo Flow for Presentations

### Flow 1: Customer Experience (ShopTrust)

1. **Login** as `customer@demo.com`
2. **Browse Products** - Notice trust scores and AI verification badges
3. **View Reviews** - See color-coded genuine (green) and fake (red) reviews with confidence scores
4. **Write a Review**:
   - Add a genuine review: "Great product! Been using for 2 weeks. Build quality is excellent."
   - Watch the **real-time AI analysis animation**
   - See the confidence score and verdict
5. **Compare Products** - Use trust rankings to find most reliable products

### Flow 2: Admin Analytics (ReviewGuard)

1. **Login** as `admin@demo.com`
2. **View Dashboard** - See detection statistics and analytics
3. **Review Detection Results**:
   - Genuine reviews (green badges with high confidence)
   - Fake reviews (red badges with detection reasons)
4. **Upload Bulk Reviews** (CSV):
   - Test with sample CSV containing mixed reviews
   - Watch AI process and classify each review
5. **View Analytics** - Charts showing detection accuracy and trends

### Flow 3: Side-by-Side Comparison

1. Open ShopTrust in one browser window
2. Open ReviewGuard admin in another
3. Write a review in ShopTrust
4. Immediately see it appear in ReviewGuard admin with analysis

---

## ✨ Key Features to Showcase

### Visual Enhancements (Option 1)

✅ **Color-Coded Reviews**
- 🟢 Green: Genuine reviews (high confidence)
- 🟡 Yellow: Suspicious reviews (medium confidence)
- 🔴 Red: Fake reviews (high fake probability)

✅ **Real-Time Detection Animation**
- Live progress bar during analysis
- Confidence score reveal
- Verdict announcement with visual feedback

✅ **Trust Scores on Products**
- Percentage-based trust ratings
- AI verification badges
- Genuine vs. fake review counts

✅ **ReviewGuard Branding**
- "Powered by ReviewGuard" banner
- Demo environment indicators
- Admin console quick access

### Demo Data (Option 2)

✅ **Realistic Product Catalog**
- 12 products across 6 categories
- Varied price ranges (₹299 - ₹4999)
- Professional descriptions

✅ **Mixed Review Patterns**
- **Genuine Reviews**: Natural language, specific details, varied ratings
  - Example: "I've been using this for 2 weeks now. Build quality is solid..."
- **Fake Reviews**: Generic praise, excessive exclamation marks, suspicious patterns
  - Example: "Amazing!!! Best ever!!!! Everyone should buy!!!!"

✅ **Complete User Journeys**
- Customer orders with purchase history
- Review patterns tied to purchases
- Behavioral metadata analysis

---

## 🛠️ Demo Management

### Reset Demo Data

To start fresh for a new demo session:

```bash
# Method 1: Via Script
docker-compose exec backend python /app/scripts/seed_demo_data.py reset
docker-compose exec backend python /app/scripts/seed_demo_data.py

# Method 2: Via API (as admin)
curl -X POST http://localhost:8000/api/admin/demo/reset \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Check System Health

```bash
# Backend health
curl http://localhost:8000/health

# ML service health
curl http://localhost:8501/health

# View model card
curl http://localhost:8501/model-card
```

---

## 📊 What Makes This Demo Impressive

### 1. **Multimodal AI Detection**
- Text analysis (DistilBERT/linguistic features)
- Metadata analysis (behavioral patterns)
- Attention fusion (combines modalities intelligently)

### 2. **Real-Time Visualization**
- Live confidence scores
- Animated detection process
- Color-coded results

### 3. **Explainable AI**
- LIME text explanations
- SHAP metadata importance
- Attention weights visualization

### 4. **Professional UI/UX**
- Modern design with Tailwind CSS
- Smooth animations
- Responsive layout
- Clear visual hierarchy

### 5. **Complete E-commerce Flow**
- Product browsing
- Shopping cart
- Order management
- Review system with AI protection

---

## 🎨 Customization Tips

### Add More Products

Edit `/app/scripts/seed_demo_data.py` and add to `DEMO_PRODUCTS` list:

```python
{
    "name": "Your Product Name",
    "category": "Electronics",  # Electronics, Sports, Food, Books, etc.
    "price": 1999,
    "description": "Product description",
    "keywords": "keyword1, keyword2"
}
```

### Adjust Genuine/Fake Ratio

In `seed_demo_data.py`, modify the distribution:

```python
# Default: 70% genuine, 30% fake
num_genuine = int(num_reviews * 0.7)
num_fake = num_reviews - num_genuine

# For more fake reviews (demo extreme scenarios):
num_genuine = int(num_reviews * 0.5)  # 50/50 split
```

---

## 🐛 Troubleshooting

### No Products Showing
```bash
# Re-run seed script
docker-compose exec backend python /app/scripts/seed_demo_data.py
```

### Reviews Not Getting Analyzed
```bash
# Check ML service is running
curl http://localhost:8501/health

# Check backend can reach ML service
docker-compose logs backend | grep ML_SERVICE_URL
```

### Login Issues
- Ensure you're using correct credentials: `admin@demo.com` / `demo123`
- Check database is initialized: `docker-compose logs db`

---

## 📈 Demo Presentation Tips

1. **Start with the Problem**: Explain fake review epidemic
2. **Show ShopTrust**: Demonstrate the user experience
3. **Reveal ReviewGuard**: Show the admin console and detection
4. **Live Demo**: Write a review and watch AI analyze it
5. **Technical Deep Dive**: Explain multimodal approach
6. **Results**: Show accuracy metrics and confidence scores

---

## 🎓 Technical Architecture

```
┌─────────────────┐
│   Frontend      │  React 19 + Vite + Tailwind
│   (Port 3000)   │  • ShopTrust (Demo UI)
└────────┬────────┘  • ReviewGuard (Admin)
         │
         │ REST API
         ▼
┌─────────────────┐
│   Backend       │  FastAPI + PostgreSQL
│   (Port 8000)   │  • Auth & User Management
└────────┬────────┘  • Product & Order API
         │           • Review Submission
         │
         │ ML Inference
         ▼
┌─────────────────┐
│  ML Service     │  FastAPI + PyTorch
│  (Port 8501)    │  • Text Model (DistilBERT)
└─────────────────┘  • Metadata Model (XGBoost)
                     • Fusion Model (Attention)
```

---

## 📝 Additional Resources

- **Main README**: `/app/README.md`
- **Demo Credentials**: `/app/DEMO_CREDENTIALS.md`
- **API Documentation**: http://localhost:8000/docs (when running)
- **ML Model Card**: http://localhost:8501/model-card

---

## 🎉 Success Indicators

Your demo is working perfectly when:

✅ Products display with trust scores
✅ Reviews show color-coded confidence badges
✅ New reviews get analyzed with animation
✅ Admin console shows detection statistics
✅ "Powered by ReviewGuard" branding visible
✅ Real-time confidence scores appear

---

**Need Help?** Check logs:
```bash
docker-compose logs -f backend
docker-compose logs -f ml_inference
docker-compose logs -f frontend
```

**Happy Demoing! 🚀**
