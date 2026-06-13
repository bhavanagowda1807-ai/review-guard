"""Pickle-stable text feature helpers (kept in their own module so unpickling
the upgraded text classifier always resolves the right symbols regardless of
how the training script was invoked)."""
from __future__ import annotations

import re
from typing import List

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


SUPERLATIVE_RE = re.compile(
    r"\b(best|worst|amazing|perfect|incredible|fantastic|terrible|awful|"
    r"horrible|outstanding|excellent|garbage|scam|fraud|wow|love)\b",
    flags=re.I,
)
PRONOUN_RE = re.compile(
    r"\b(I|we|you|he|she|they|us|me|him|her|them|my|our)\b", flags=re.I,
)
POSITIVE_RE = re.compile(
    r"\b(good|great|excellent|love|amazing|perfect|nice|happy|recommend)\b", re.I,
)
NEGATIVE_RE = re.compile(
    r"\b(bad|terrible|awful|hate|poor|worst|broken|scam|return)\b", re.I,
)
EXCLAIM_RE = re.compile(r"!+")


def linguistic_features(texts: List[str], ratings=None) -> np.ndarray:
    """Hand-crafted style + sentiment features per text."""
    if ratings is None:
        ratings = [3.0] * len(texts)

    rows = []
    for text, rating in zip(texts, ratings):
        t = str(text or "")
        words = re.findall(r"\w+", t)
        n_words = max(len(words), 1)
        caps_words = [w for w in words if len(w) > 2 and w.isupper()]
        sentences = [s.strip() for s in re.split(r"[.!?]+", t) if s.strip()]

        n_super = len(SUPERLATIVE_RE.findall(t))
        n_pron = len(PRONOUN_RE.findall(t))
        n_pos = len(POSITIVE_RE.findall(t))
        n_neg = len(NEGATIVE_RE.findall(t))
        n_excl = len(EXCLAIM_RE.findall(t))
        sent_score = (n_pos - n_neg) / max(n_pos + n_neg, 1)
        expected = (float(rating) - 3.0) / 2.0
        mismatch = abs(sent_score - expected)
        sent_lengths = [len(re.findall(r"\w+", s)) for s in sentences]
        sent_var = float(np.var(sent_lengths)) if sent_lengths else 0.0

        rows.append([
            n_words,
            float(np.mean([len(w) for w in words])) if words else 0.0,
            len(caps_words) / n_words,
            n_super / n_words,
            n_pron / n_words,
            n_excl / max(len(t), 1) * 100,
            sent_var,
            mismatch,
            t.count("!"),
            t.count("?"),
            len(set(words)) / n_words,
        ])
    return np.asarray(rows, dtype=np.float32)


def text_only_col(df):
    """Pull just the text column out of an incoming DataFrame."""
    return df["text"].astype(str).tolist()


class LinguisticFeatures(BaseEstimator, TransformerMixin):
    """sklearn transformer wrapping :func:`linguistic_features`."""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        if isinstance(X, pd.DataFrame):
            texts = X["text"].astype(str).tolist()
            ratings = (X["rating"].astype(float).tolist()
                       if "rating" in X.columns else None)
            return linguistic_features(texts, ratings)
        return linguistic_features(list(X))
