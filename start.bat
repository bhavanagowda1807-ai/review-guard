@echo off
title ReviewGuard - Starting...
color 0A
echo.
echo  ============================================
echo   ReviewGuard - Fake Review Detection
echo  ============================================
echo.
cd /d "C:\Users\Bhavana\Downloads\reviewguard-main"
echo [1/7] Starting all containers...
docker compose up -d
echo  Done!
echo.
echo [2/7] Waiting for containers to be ready...
timeout /t 20 /nobreak >nul
echo  Done!
echo.
echo [3/7] Fixing CORS settings...
docker compose exec backend sh -c "grep -q 'CORS_ORIGINS=*' /app/.env || echo 'CORS_ORIGINS=*' >> /app/.env"
docker compose restart backend
timeout /t 8 /nobreak >nul
echo  Done!
echo.
echo [4/7] Verifying ML models are loaded...
docker compose exec ml_inference python -c "import pickle, os; [print(f'  OK: {f}') for f in ['text_classifier.pkl','metadata_classifier.pkl','fusion_classifier.pkl'] if os.path.exists(f'/app/saved_models/{f}')]"
echo  Done!
echo.
echo [5/7] Copying improved inference adapter...
docker compose cp "ml_service/improved" ml_inference:/app/improved
echo  Done!
echo.
echo [6/7] Restarting ML service to ensure models are active...
docker compose restart ml_inference
timeout /t 10 /nobreak >nul
echo  Done!
echo.
echo [7/7] Seeding demo data (products, users, reviews)...
docker compose exec backend python /app/seed_demo_data.py
echo  Done!
echo.
echo  ============================================
echo   ReviewGuard Demo is Ready!
echo  ============================================
echo.
echo   Open your browser: http://localhost:3000
echo.
echo   DEMO ACCOUNTS
echo   --------------------------------
echo   Admin:    username: admin  ^|  password: admin123
echo   Seller:   Register on ShopTrust as Seller
echo   Customer: Register on ShopTrust as Customer
echo.
echo   TWO PLATFORMS:
echo   - ReviewGuard : AI Detection Console (Admin only)
echo               Login via "Admin Console" on landing page
echo   - ShopTrust   : Live Demo Marketplace
echo               Login via "Try Demo" on landing page
echo.
echo   KEY FEATURES:
echo   - CSV bulk upload with AI detection
echo   - Explain button on fake reviews (confidence,
echo     linguistic signals, metadata signals)
echo   - Instant Clear Dataset (bulk delete)
echo   - ShopTrust: customer reviews only (no admin data)
echo   - Owner dashboard scoped to own products
echo   - ROC chart cleaned up (Image bar removed)
echo   - Multimodal AI: Text + Metadata fusion
echo     Text: 87.5%% accuracy / 0.913 AUC
echo     Metadata: 96.0%% accuracy / 0.963 AUC
echo     Fusion: 96.0%% accuracy / 0.959 AUC
echo.
echo  ============================================
echo.
start http://localhost:3000
pause
