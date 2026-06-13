#!/usr/bin/env bash
# Run training for text, image, metadata, and fusion with MLflow tracking.
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
cd ml_service
python train/train.py --module text --mlflow --mlflow-uri http://localhost:5000
python train/train.py --module image --mlflow --mlflow-uri http://localhost:5000
python train/train.py --module metadata --mlflow --mlflow-uri http://localhost:5000
python train/train.py --module fusion --mlflow --mlflow-uri http://localhost:5000
