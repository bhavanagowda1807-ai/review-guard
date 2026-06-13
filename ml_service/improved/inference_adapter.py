"""Inference adapters for the upgraded ML pipelines.

The new pipelines have different input contracts than the legacy
`TextModel.predict()` / `MetadataModel.predict()` / `FusionModel.predict()`
code expects:

* New text classifier expects a `DataFrame` with `text` and `rating` columns
  (because it concatenates word + char TF-IDF with linguistic features that
  use the rating to compute the sentiment-rating mismatch feature).
* New metadata classifier expects a `numpy` array of 10 features in the
  fixed `METADATA_COLS` order.
* New fusion classifier expects `[text_fake_prob, meta_fake_prob]`.

This module provides thin wrappers so the existing `ml_service/models/*.py`
classes can transparently call the upgraded pipelines. To plug them in,
patch the `_load_classifier` method (or call the adapter from `.predict`).

NOTE: when unpickling the upgraded text pipeline, the linguistic feature
extractor and the `_text_only_col` helper must be importable, so
``import ml_service.improved.train_all`` (or this module) is needed at
inference startup.
"""
from __future__ import annotations

import os
import pickle
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# Re-export the symbols pickle needs to resolve when loading text_classifier.pkl
from improved.text_features import (  # noqa: F401
    LinguisticFeatures, linguistic_features, text_only_col,
)

SAVED_MODELS = Path(__file__).resolve().parent.parent / "saved_models"

METADATA_COLS = [
    "account_age", "reviews_per_day", "verified_purchase_ratio",
    "rating_deviation", "burstiness", "helpfulness_ratio",
    "similarity_score", "sentiment_rating_mismatch",
    "night_review_ratio", "reviewer_overlap_score",
]


def _load(name: str):
    path = SAVED_MODELS / f"{name}.pkl"
    if not path.exists():
        return None
    with open(path, "rb") as f:
        return pickle.load(f)


class TextAdapter:
    """Wraps the upgraded text pipeline behind a `predict(text, rating)` API."""

    def __init__(self):
        self.model = _load("text_classifier")

    def predict_fake_prob(self, text: str, rating: float = 3.0) -> float:
        if self.model is None:
            return 0.5
        df = pd.DataFrame([{"text": str(text or ""), "rating": float(rating or 3)}])
        return float(self.model.predict_proba(df)[0, 1])

    def predict_genuine_prob(self, text: str, rating: float = 3.0) -> float:
        return 1.0 - self.predict_fake_prob(text, rating)


class MetadataAdapter:
    """Wraps the upgraded metadata pipeline behind a `predict(dict)` API."""

    def __init__(self):
        self.model = _load("metadata_classifier")

    def features_from_dict(self, d: dict) -> np.ndarray:
        return np.array([[float(d.get(k, 0.0)) for k in METADATA_COLS]])

    def predict_fake_prob(self, d: dict) -> float:
        if self.model is None:
            return 0.5
        return float(self.model.predict_proba(self.features_from_dict(d))[0, 1])

    def predict_genuine_prob(self, d: dict) -> float:
        return 1.0 - self.predict_fake_prob(d)


class FusionAdapter:
    """Calibrated stacking fusion over [text_fake_prob, meta_fake_prob]."""

    def __init__(self, threshold: float = 0.5):
        self.model = _load("fusion_classifier")
        self.threshold = threshold

    def predict(self, text_fake_prob: float, meta_fake_prob: float) -> dict:
        if self.model is None:
            p = 0.5 * (text_fake_prob + meta_fake_prob)
        else:
            arr = np.array([[float(text_fake_prob), float(meta_fake_prob)]])
            p = float(self.model.predict_proba(arr)[0, 1])
        verdict = "fake" if p >= self.threshold else "genuine"
        conf = p if verdict == "fake" else 1.0 - p
        return {
            "verdict": verdict,
            "confidence": float(conf),
            "fake_probability": float(p),
            "genuine_probability": float(1.0 - p),
            "fusion_strategy": "calibrated_stacking",
        }


def smoke_test():
    """Quick sanity check that the upgraded artifacts produce useful probs."""
    t = TextAdapter()
    m = MetadataAdapter()
    f = FusionAdapter()

    cases = [
        # (text, rating, meta_dict, expected)
        ("Bought this last month, battery lasts about two days, would buy again.",
         4,
         dict(account_age=420, reviews_per_day=0.1, verified_purchase_ratio=0.85,
              rating_deviation=0.4, burstiness=0.5, helpfulness_ratio=0.7,
              similarity_score=0.1, sentiment_rating_mismatch=0.05,
              night_review_ratio=0.1, reviewer_overlap_score=0.05),
         "genuine"),
        ("AMAZING product!!! BEST EVER!!! BUY NOW!!!", 5,
         dict(account_age=10, reviews_per_day=3.0, verified_purchase_ratio=0.1,
              rating_deviation=1.8, burstiness=4.0, helpfulness_ratio=0.1,
              similarity_score=0.9, sentiment_rating_mismatch=0.6,
              night_review_ratio=0.8, reviewer_overlap_score=0.7),
         "fake"),
    ]

    for text, rating, meta, expected in cases:
        tp = t.predict_fake_prob(text, rating)
        mp = m.predict_fake_prob(meta)
        out = f.predict(tp, mp)
        print(f"expected={expected:8s} text_fake={tp:.3f} meta_fake={mp:.3f} -> {out}")


if __name__ == "__main__":
    smoke_test()
