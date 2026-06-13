import os
import re
import numpy as np
from train.utils import load_model

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'saved_models', 'text_classifier.pkl')


def _try_load_upgraded():
    """Return the upgraded sklearn Pipeline if it exists, else None."""
    try:
        from improved.text_features import LinguisticFeatures, text_only_col  # noqa: F401
        import pickle
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, "rb") as f:
                obj = pickle.load(f)
            from sklearn.pipeline import Pipeline as _SkPipeline
            if isinstance(obj, _SkPipeline):
                return obj
    except Exception:
        return None
    return None


class TextModel:
    def __init__(self, model_name='distilbert-base-uncased'):
        self.device = None
        self.tokenizer = None
        self.model = None
        if os.getenv("LOAD_DEEP_MODELS", "false").lower() == "true":
            try:
                import torch
                from transformers import AutoModel, AutoTokenizer

                self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModel.from_pretrained(model_name).to(self.device)
                self.model.eval()
            except Exception as exc:
                print(f"Text encoder unavailable, using linguistic fallback: {exc}")
        # Prefer the upgraded sklearn pipeline if present; otherwise fall back
        # to the legacy single-feature classifier path.
        self.upgraded = _try_load_upgraded()
        self.classifier = None if self.upgraded is not None else self._load_classifier()

    def _load_classifier(self):
        if os.path.exists(MODEL_PATH):
            try:
                return load_model(MODEL_PATH)
            except Exception:
                return None
        return None

    def embed(self, text: str):
        if self.model is None or self.tokenizer is None:
            features = np.array([
                self.count_superlatives(text),
                self.readability_score(text),
                self.sentence_variance(text),
                self.pronoun_ratio(text),
                len(re.findall(r'\w+', text or '')),
            ], dtype=np.float32)
            return np.pad(features, (0, max(0, 32 - len(features))))[:32]
        import torch

        inputs = self.tokenizer(text or '', return_tensors='pt', truncation=True, padding=True, max_length=256).to(self.device)
        with torch.no_grad():
            out = self.model(**inputs)
        return out.last_hidden_state.mean(dim=1).cpu().numpy()[0]

    def readability_score(self, text: str):
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        words = re.findall(r'\w+', text)
        syllables = sum(self._count_syllables(word) for word in words)
        if not sentences or not words:
            return 0.0
        words_per_sentence = len(words) / len(sentences)
        syllables_per_word = syllables / len(words)
        return 206.835 - 1.015 * words_per_sentence - 84.6 * syllables_per_word

    def _count_syllables(self, word: str):
        word = word.lower()
        vowels = 'aeiouy'
        count = 0
        prev_vowel = False
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        if word.endswith('e') and count > 1:
            count -= 1
        return count or 1

    def pronoun_ratio(self, text: str):
        pronouns = re.findall(r"\b(I|we|you|he|she|they|us|me|him|her|them)\b", text, flags=re.I)
        words = re.findall(r'\w+', text)
        return len(pronouns) / max(len(words), 1)

    def count_superlatives(self, text: str):
        return len(re.findall(r'\b(best|worst|amazing|perfect|incredible|fantastic|terrible|awful)\b', text, flags=re.I))

    def sentence_variance(self, text: str):
        sentences = [s.strip() for s in re.split(r'[.!?]', text) if s.strip()]
        lengths = [len(re.findall(r'\w+', s)) for s in sentences]
        return float(np.var(lengths)) if lengths else 0.0

    def sentiment_mismatch(self, text: str, rating: float = None):
        if rating is None:
            return 0.0
        positive = len(re.findall(r'\b(good|great|excellent|love|amazing|perfect)\b', text, flags=re.I))
        negative = len(re.findall(r'\b(bad|terrible|awful|hate|poor|worst)\b', text, flags=re.I))
        if positive + negative == 0:
            return 0.0
        sentiment = (positive - negative) / (positive + negative)
        expected = (rating - 3.5) / 1.5 if rating is not None else 0.0
        return abs(sentiment - expected)

    def score_from_features(self, features, embedding=None):
        score = 0.5
        score -= min(features['superlative_count'], 3) * 0.03
        score -= min(features['sentiment_mismatch'], 1.0) * 0.1
        score -= (max(features['readability'], 0) < 50) * 0.05
        score -= min(features['sentence_variance'], 10) * 0.01
        score += max(0.2 - features['pronoun_ratio'], 0) * 0.1
        if self.model is not None and embedding is not None:
            try:
                import torch
                deep_score = float(torch.sigmoid(torch.tensor(np.mean(embedding), dtype=torch.float32)).clamp(0.0, 1.0))
                score = float(np.clip(0.55 * score + 0.45 * deep_score, 0.0, 1.0))
            except Exception:
                pass
        return float(np.clip(score, 0.0, 1.0))

    def predict(self, text: str, rating: float = None):
        embedding = self.embed(text)
        features = {
            'superlative_count': self.count_superlatives(text),
            'readability': self.readability_score(text),
            'sentence_variance': self.sentence_variance(text),
            'pronoun_ratio': self.pronoun_ratio(text),
            'sentiment_mismatch': self.sentiment_mismatch(text, rating),
        }
        confidence = self.score_from_features(features, embedding)

        # ----- Upgraded sklearn pipeline (preferred) ------------------------
        if self.upgraded is not None:
            try:
                import pandas as pd
                df = pd.DataFrame([{
                    "text": str(text or ""),
                    "rating": float(rating if rating is not None else 3.0),
                }])
                classes = list(getattr(self.upgraded, "classes_", [0, 1]))
                # Pipeline.classes_ may be missing; fall back to last step.
                if not classes:
                    last = self.upgraded.steps[-1][1]
                    classes = list(getattr(last, "classes_", [0, 1]))
                genuine_index = classes.index(0) if 0 in classes else 0
                confidence = float(self.upgraded.predict_proba(df)[0, genuine_index])
            except Exception:
                pass

        # ----- Legacy single-feature classifier (only if no upgrade) --------
        elif self.classifier is not None:
            try:
                if hasattr(self.classifier, "n_features_in_") and self.classifier.n_features_in_ == len(embedding):
                    input_vector = [embedding.tolist()]
                else:
                    input_vector = [[confidence]]
                classes = list(getattr(self.classifier, "classes_", [0, 1]))
                genuine_index = classes.index(0) if 0 in classes else 0
                confidence = float(self.classifier.predict_proba(input_vector)[0, genuine_index])
            except Exception:
                pass

        if self.model is not None:
            features['deep_embedding_mean'] = float(np.mean(embedding))
        return {
            'score': confidence,
            'details': f"Superlatives={features['superlative_count']}, readability={features['readability']:.1f}, mismatch={features['sentiment_mismatch']:.2f}",
            'features': features,
            'embedding': embedding.tolist() if hasattr(embedding, 'tolist') else embedding,
        }
