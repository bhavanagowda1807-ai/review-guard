import os
import numpy as np
from train.utils import load_model

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'saved_models', 'metadata_classifier.pkl')

# All 10 metadata features used by the classifier
META_FEATURE_NAMES = [
    'account_age',
    'reviews_per_day',
    'verified_purchase_ratio',
    'rating_deviation',
    'burstiness',
    'helpfulness_ratio',
    'similarity_score',
    'sentiment_rating_mismatch',
    'night_review_ratio',
    'reviewer_overlap_score',
]


class MetadataModel:
    def __init__(self):
        self.classifier = self._load_classifier()

    def _load_classifier(self):
        if os.path.exists(MODEL_PATH):
            try:
                return load_model(MODEL_PATH)
            except Exception:
                return None
        return None

    def normalize(self, value, low, high):
        if high == low:
            return 0.0
        return float(np.clip((value - low) / (high - low), 0.0, 1.0))

    def features_from_dict(self, features: dict):
        return np.array([[features.get(k, 0.0) for k in META_FEATURE_NAMES]])

    def predict(self, features: dict):
        # ── Original 6 features ──────────────────────────────────
        account_age      = self.normalize(features.get('account_age', 0.0), 0, 365)
        reviews_per_day  = 1 - self.normalize(features.get('reviews_per_day', 0.0), 0, 5)
        verified_ratio   = self.normalize(features.get('verified_purchase_ratio', 0.0), 0, 1)
        rating_deviation = 1 - self.normalize(abs(features.get('rating_deviation', 0.0)), 0, 2)
        burstiness       = 1 - self.normalize(features.get('burstiness', 0.0), 0, 5)
        helpfulness      = self.normalize(features.get('helpfulness_ratio', 0.0), 0, 1)

        # ── New 4 features ───────────────────────────────────────
        # All 4 are "bad" signals so invert: higher raw value = more fake = lower genuine score
        similarity        = 1 - self.normalize(features.get('similarity_score', 0.0), 0, 1)
        sentiment_mismatch = 1 - self.normalize(features.get('sentiment_rating_mismatch', 0.0), 0, 1)
        night_ratio       = 1 - self.normalize(features.get('night_review_ratio', 0.0), 0, 1)
        overlap           = 1 - self.normalize(features.get('reviewer_overlap_score', 0.0), 0, 1)

        # Weighted sum — new features take 30% of total weight
        score = float(np.clip(
            0.15 * account_age        +
            0.15 * reviews_per_day    +
            0.15 * verified_ratio     +
            0.10 * rating_deviation   +
            0.10 * burstiness         +
            0.05 * helpfulness        +
            0.10 * similarity         +
            0.08 * sentiment_mismatch +
            0.07 * night_ratio        +
            0.05 * overlap,
            0.0, 1.0
        ))

        # Use trained classifier if available (overrides heuristic score)
        if self.classifier is not None:
            try:
                classes = list(getattr(self.classifier, "classes_", [0, 1]))
                genuine_index = classes.index(0) if 0 in classes else 0
                score = float(self.classifier.predict_proba(
                    self.features_from_dict(features)
                )[0, genuine_index])
            except Exception:
                pass

        explain = {
            'account_age':               account_age,
            'reviews_per_day':           reviews_per_day,
            'verified_purchase_ratio':   verified_ratio,
            'rating_deviation':          rating_deviation,
            'burstiness':               burstiness,
            'helpfulness_ratio':         helpfulness,
            'similarity_score':          similarity,
            'sentiment_rating_mismatch': sentiment_mismatch,
            'night_review_ratio':        night_ratio,
            'reviewer_overlap_score':    overlap,
        }
        return {'score': score, 'explain': explain}
