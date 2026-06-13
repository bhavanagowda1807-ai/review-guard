import os
from typing import Any

import httpx
from celery import Celery

broker = os.getenv("REDIS_URL", "redis://redis:6379/0")
celery_app = Celery("fake_review_worker", broker=broker, backend=broker)


@celery_app.task(name="run_inference_task")
def run_inference_task(payload: dict[str, Any]) -> dict[str, Any]:
    ml_url = os.getenv("ML_SERVICE_URL", "http://ml_inference:8501")
    if not ml_url.endswith('/predict'):
        ml_url = ml_url.rstrip('/') + '/predict'

    # Send only text + metadata fields — image fields removed
    allowed_keys = {
        "text", "rating", "account_age", "reviews_per_day",
        "verified_purchase_ratio", "rating_deviation",
        "burstiness", "helpfulness_ratio", "fusion_strategy",
    }
    data = {
        key: str(value)
        for key, value in payload.items()
        if key in allowed_keys and value is not None
    }

    with httpx.Client(timeout=60.0) as client:
        response = client.post(ml_url, data=data)
        response.raise_for_status()
        return response.json()
