#!/bin/bash
set -e
echo "Running model initialization..."
python /app/init_models.py
echo "Starting inference server..."
exec uvicorn inference:app --host 0.0.0.0 --port 8501
