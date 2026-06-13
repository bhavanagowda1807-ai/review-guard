# Multimodal Fake Review Detection System

Full-stack research-oriented system for detecting fake e-commerce reviews with text, image, metadata, late-fusion, and attention-based multimodal scoring.

Services:
- `frontend`: React 19 + Vite + Tailwind dark AI dashboard
- `backend`: FastAPI REST API, JWT auth, PostgreSQL models, Celery job endpoints
- `worker`: Celery + Redis async inference executor
- `ml_inference`: FastAPI + PyTorch-style inference and explainability service
- `db`, `redis`, `mlflow`: PostgreSQL, queue backend, and experiment tracking

Quickstart
1. Copy `.env.example` to `.env` and fill values.
2. Build and start services:

```bash
docker-compose up --build
```

3. Visit frontend at `http://localhost:3000`.
4. Backend API is available at `http://localhost:8000`.
5. ML inference service is available at `http://localhost:8501/predict`.
6. MLflow is available at `http://localhost:5000`.

The first registered user is treated as an admin when no initial admin credentials are configured. If you want a demo admin, set `INITIAL_ADMIN_USERNAME` and `INITIAL_ADMIN_PASSWORD` in `.env` before startup.

The Compose setup now shares MLflow inside the network, so the backend and worker use `http://mlflow:5000` for experiment tracking.

### Deployment

Start the full deployment with:

```bash
make deploy
```

Or use the helper script directly:

```bash
./scripts/compose_up.sh
```

If Docker is not available, install Docker Desktop or a compatible Docker Engine before running these commands.

The `ml_service/saved_models` directory is mounted into the `ml_inference` container, so trained artifacts placed there are available to the running inference service. Set `LOAD_DEEP_MODELS=true` when you want the service to load DistilBERT, EfficientNet, and CLIP weights; the default fallback mode keeps local development fast and deterministic.

For model artifact naming and container mount details, see `ml_service/README.md`.

API endpoints:

- `POST /auth/register`
- `POST /auth/login`
- `POST /api/predict`
- `POST /api/predict/async`
- `GET /api/predict/tasks/{task_id}`
- `GET /api/reviews`
- `GET /health`
- `GET /api/health`
- `GET http://localhost:8501/model-card`
- `POST http://localhost:8501/explain/text`
- `POST http://localhost:8501/explain/image`
- `POST http://localhost:8501/explain/metadata`
- `POST http://localhost:8501/explain/attention`

Training and evaluation:

```bash
cd ml_service
python train/train.py --module text
python train/train.py --module image
python train/train.py --module metadata
python train/train.py --module fusion
python train/evaluate.py --module fusion
```

For one-shot replayable training on the current repository, run:

```bash
./scripts/train_all.sh
```

Use `--mlflow --mlflow-uri http://localhost:5000` to log artifacts to MLflow if the server is available.

Deep research training:

```bash
cd ml_service
python train/train_text_transformer.py --text-data path/to/text.csv --model-name distilbert-base-uncased
python train/train_text_transformer.py --text-data path/to/text.csv --model-name roberta-base
python train/train_image_cnn.py --image-data path/to/images_or_manifest --arch efficientnet_b0
python train/train_image_cnn.py --image-data path/to/images_or_manifest --arch resnet18
```

Database migrations:

```bash
cd backend
alembic upgrade head
```

Tests:

```bash
make test
# or
python -m pytest backend/tests ml_service/tests
```

Verify the full repository flow:

```bash
make verify
```

The repository includes `pytest.ini` at the root, so local temp files are created under `.pytest` instead of the system temp directory on Windows.

```bash
cd frontend && npm run build
```

On Windows:

```powershell
.\scripts\verify.ps1
```

If local PowerShell script execution is disabled:

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\verify.ps1
```

To track training and model artifacts in MLflow, add `--mlflow --mlflow-uri http://localhost:5000`.

Explainability endpoints are available through the backend proxy at:

- `POST /api/explain/text`
- `POST /api/explain/image`
- `POST /api/explain/metadata`
- `POST /api/explain/attention`

You can also call the ML inference service directly at `http://localhost:8501` for debugging.

Dataset contracts:

- Text CSV: `text`, `rating`, `label` where `0=genuine`, `1=fake`.
- Metadata CSV: `account_age`, `reviews_per_day`, `verified_purchase_ratio`, `rating_deviation`, `burstiness`, `helpfulness_ratio`, `label`.
- Image manifest CSV: `image_path`, `label`, optional `caption`. Place it at `manifest.csv` inside an image dataset folder or pass the manifest path directly.
- Image folders are also supported with `genuine/`, `real/`, `fake/`, or `spam/` subdirectories.

Research modules:

- Text: DistilBERT/RoBERTa-compatible embedding path plus linguistic deception features.
- Image: EfficientNet-B0/ResNet-ready path, perceptual hash, CLIP consistency, ELA heatmap, authenticity score.
- Metadata: XGBoost/MLP-compatible behavioral classifier.
- Fusion: late-fusion baseline and missing-modality-aware attention fusion.
- Explainability: LIME text weights, SHAP metadata explanations, Grad-CAM/ELA image heatmaps, attention visualization.

Version baseline:

- React `19.2.6`
- FastAPI `0.136.1`
- PyTorch `2.12.0`
- TorchVision `0.27.0`
- PostgreSQL `17-alpine`
- Redis `7.4-alpine`

Training artifacts:

- Every classifier pickle saved by `ml_service/train/train.py` now receives a sibling `*.card.json` file containing module name, UTC creation time, metrics, feature names, and label semantics.
- When `--mlflow` is enabled, both the model and its card are logged to MLflow.
- `/model-card` lists saved model cards and artifacts from `ml_service/saved_models`.
- CI is configured in `.github/workflows/ci.yml` for Python compile/tests and frontend build.

See `docs/architecture.md` for the module layout and extension points.
