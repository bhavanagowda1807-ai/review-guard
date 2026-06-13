FROM python:3.12-slim
WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY . /app
RUN mkdir -p /app/static/uploads
RUN cat > /app/.env << 'EOF'
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/reviews_db
REDIS_URL=redis://redis:6379/0
SECRET_KEY=change-me
ML_SERVICE_URL=http://ml_inference:8501
MLFLOW_TRACKING_URI=http://mlflow:5000
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://frontend:3000
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=adminpass
EOF
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
