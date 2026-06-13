Architecture Overview

- frontend: React + Tailwind dashboard for review text, review images, profile photos, metadata, verdicts, heatmaps, ROC summaries, and modality attention.
- backend: FastAPI orchestration API with JWT auth, PostgreSQL models, synchronous inference, and Celery-backed asynchronous inference.
- worker: Celery process that sends payloads to the ML inference service through Redis task queues.
- ml_service: PyTorch-compatible inference, training, evaluation, model loading, and explainability endpoints. It can run in lightweight fallback mode or deep-model mode.
- infra: PostgreSQL, Redis, MLflow server, Docker Compose service wiring.

Module Layout

- `backend/app/api`: auth and inference routes.
- `backend/app/celery_worker.py`: async inference task definition.
- `ml_service/models/text_model.py`: DistilBERT/RoBERTa-ready embeddings plus superlatives, sentiment-rating mismatch, readability, sentence variance, and pronoun ratio.
- `ml_service/models/image_model.py`: EfficientNet-ready authenticity scoring, perceptual hash, CLIP semantic consistency, and ELA heatmap generation.
- `ml_service/models/metadata_model.py`: behavioral feature scoring and trained classifier loading.
- `ml_service/models/fusion_model.py`: late fusion baseline and attention fusion with missing-modality masks.
- `ml_service/train`: dataset loaders, training scripts, evaluation scripts, MLflow logging.
- `frontend/src/components`: dashboard controls, result cards, attention visualization, ROC comparison, heatmap, explainability panels.
- `backend/alembic`: migration environment and initial schema revision.
- `.github/workflows/ci.yml`: compile, unit test, and frontend build workflow.

ML Service Endpoints
- POST /predict: Multimodal inference with image/text/metadata
- POST /explain/text: LIME-based text explanation
- POST /explain/image: Grad-CAM image heatmap
- POST /explain/metadata: SHAP feature importance
- POST /explain/attention: Fusion attention weights

Backend Endpoints

- POST /auth/register
- POST /auth/login
- GET /auth/me
- POST /api/predict
- POST /api/predict/async
- GET /api/predict/tasks/{task_id}
- GET /api/reviews
- GET /api/health

Operational Endpoints

- GET /health on the backend service.
- GET /health on the ML inference service.
- GET /model-card on the ML inference service.

Score Semantics

Model modality scores represent estimated probability that the evidence is genuine. The final verdict is `fake` when the fused genuine probability is below 0.5. Final confidence is the certainty of the displayed verdict, so fake verdicts use `1 - genuine_probability`.

Dataset Contracts

- Text datasets accept `text`, `review`, or `review_text` aliases and normalize labels such as `fake`, `spam`, `genuine`, and `real`.
- Metadata datasets require the six behavioral feature columns plus `label`.
- Image datasets can use a `manifest.csv` with `image_path`, `label`, and optional `caption`, or subfolders named `genuine`, `real`, `fake`, or `spam`.
