"""Text + metadata fusion model (image modality removed)."""
import os
import numpy as np
from train.utils import load_model

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'saved_models', 'fusion_classifier.pkl')


class FusionModel:
    def __init__(self):
        self.classifier = self._load_classifier()

    def _load_classifier(self):
        if os.path.exists(MODEL_PATH):
            try:
                return load_model(MODEL_PATH)
            except Exception:
                return None
        return None

    def softmax(self, logits):
        exp = np.exp(logits - np.max(logits))
        return exp / exp.sum()

    def _available(self, text_score, meta_score):
        """Return names and scores for whichever modalities have values."""
        pairs = [("text", text_score), ("meta", meta_score)]
        names = [n for n, s in pairs if s is not None]
        scores = np.array([float(s) for n, s in pairs if s is not None], dtype=np.float32)
        if scores.size == 0:
            names = ["text", "meta"]
            scores = np.array([0.5, 0.5], dtype=np.float32)
        return names, scores

    def _response(self, genuine_probability, weights, strategy):
        genuine_probability = float(np.clip(genuine_probability, 0.0, 1.0))
        verdict = 'fake' if genuine_probability < 0.5 else 'genuine'
        confidence = genuine_probability if verdict == 'genuine' else 1.0 - genuine_probability
        return {
            'verdict': verdict,
            'confidence': float(confidence),
            'genuine_probability': genuine_probability,
            'attention': weights,
            'fusion_strategy': strategy,
        }

    def late_fusion(self, text_score, meta_score):
        names, scores = self._available(text_score, meta_score)
        base = {"text": 0.65, "meta": 0.35}
        raw_weights = np.array([base[n] for n in names], dtype=np.float32)
        raw_weights /= raw_weights.sum()
        genuine_probability = float(np.dot(raw_weights, scores))
        weights = {"text": 0.0, "meta": 0.0}
        weights.update({n: float(w) for n, w in zip(names, raw_weights)})
        return self._response(genuine_probability, weights, "late")

    def attention_fusion(self, text_score, _image_score_ignored, meta_score):
        """Attention fusion over text + metadata (image argument kept for compat, ignored)."""
        names, scores = self._available(text_score, meta_score)
        uncertainty = 1.0 - np.abs(scores - 0.5) * 2.0
        attention = self.softmax((1.0 - uncertainty) * 3.0)
        genuine_probability = float(np.dot(attention, scores))
        weights = {"text": 0.0, "meta": 0.0}
        weights.update({n: float(w) for n, w in zip(names, attention)})
        return self._response(genuine_probability, weights, "attention")

    def predict(self, text_score, image_score=None, meta_score=None, strategy="attention"):
        # image_score parameter accepted but ignored
        if strategy == "late":
            return self.late_fusion(text_score, meta_score)
        # Whenever a trained classifier is loaded, prefer it over the
        # heuristic attention fusion – it's the calibrated stacking model.
        if self.classifier is not None and strategy in ("trained", "attention"):
            try:
                # The upgraded fusion classifier was trained on
                # [text_fake_prob, meta_fake_prob], while text_score/meta_score
                # here are *genuine* probabilities. Flip to fake-prob space so
                # the classifier sees the same distribution it learned on.
                ts = 0.5 if text_score is None else 1.0 - float(text_score)
                ms = 0.5 if meta_score is None else 1.0 - float(meta_score)
                filled = [ts, ms]
                classes = list(getattr(self.classifier, "classes_", [0, 1]))
                genuine_index = classes.index(0) if 0 in classes else 0
                prob = float(self.classifier.predict_proba([filled])[0, genuine_index])
                return self._response(prob, {"text": 0.65, "meta": 0.35}, "trained")
            except Exception:
                pass
        return self.attention_fusion(text_score, None, meta_score)
