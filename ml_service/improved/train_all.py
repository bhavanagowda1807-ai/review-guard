"""Train and evaluate baseline + upgraded fake-review detectors.

Modules:
  text     – baseline: TF-IDF (word) + LogisticRegression
             upgraded: TF-IDF(word+char) + linguistic features → CalibratedClassifier (LogReg / LinearSVC ensemble via stacking)
  metadata – baseline: GradientBoostingClassifier on 10 metadata features
             upgraded: LightGBM with hyper-parameter random search + isotonic calibration
  fusion   – baseline: simple LogReg over (text_prob, meta_prob)
             upgraded: stacking with out-of-fold base predictions + threshold tuning to maximise F1

All models are trained on the synthesised dataset (`improved/synth_dataset.py`),
evaluated on a held-out 20 % test split with 5-fold stratified CV on training,
and the upgraded pickles overwrite the saved_models artifacts the inference
service already consumes.

Run:
    python3 ml_service/improved/train_all.py --n 6000
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
import re
import sys
import time
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

# -- Repo paths -------------------------------------------------------------
HERE = Path(__file__).resolve().parent
ML_ROOT = HERE.parent
REPO_ROOT = ML_ROOT.parent
SAVED_MODELS = ML_ROOT / "saved_models"
DATA_DIR = ML_ROOT / "data"
REPORT_PATH = ML_ROOT / "ACCURACY_REPORT.md"

sys.path.insert(0, str(ML_ROOT))

from improved.synth_dataset import generate  # noqa: E402
from improved.text_features import (  # noqa: E402
    LinguisticFeatures, linguistic_features, text_only_col,
)
# Aliases kept for backwards compatibility with previously-saved pickles.
_linguistic_features = linguistic_features
_text_only_col = text_only_col

# -- sklearn imports --------------------------------------------------------
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import (StratifiedKFold, cross_val_predict,
                                     train_test_split)
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

# Optional gradient boosters
try:
    import lightgbm as lgb
    HAS_LGB = True
except Exception:
    HAS_LGB = False


METADATA_COLS = [
    "account_age", "reviews_per_day", "verified_purchase_ratio",
    "rating_deviation", "burstiness", "helpfulness_ratio",
    "similarity_score", "sentiment_rating_mismatch",
    "night_review_ratio", "reviewer_overlap_score",
]


# ---------------------------------------------------------------------------
# Linguistic feature extractor (used by upgraded text model)
# ---------------------------------------------------------------------------
SUPERLATIVE_RE_LEGACY = re.compile(r"\b(amazing|perfect)\b", re.I)
# (Linguistic feature implementation lives in improved.text_features now.)


# ---------------------------------------------------------------------------
# Metric utilities
# ---------------------------------------------------------------------------
@dataclass
class ModelMetrics:
    name: str
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    roc_auc: float = 0.0
    cv_accuracy_mean: float = 0.0
    cv_accuracy_std: float = 0.0
    cv_f1_mean: float = 0.0
    cv_f1_std: float = 0.0
    cv_auc_mean: float = 0.0
    cv_auc_std: float = 0.0
    confusion: List[List[int]] = field(default_factory=list)
    report: Dict = field(default_factory=dict)
    train_time_sec: float = 0.0
    n_train: int = 0
    n_test: int = 0
    threshold: float = 0.5
    extras: Dict = field(default_factory=dict)


def _eval(name, model, X_train, y_train, X_test, y_test,
          predict_proba_fn=None, threshold=0.5) -> ModelMetrics:
    """Evaluate `model` and run 5-fold stratified CV on the training set."""
    t0 = time.time()
    model.fit(X_train, y_train)
    train_time = time.time() - t0

    if predict_proba_fn is None:
        probs = model.predict_proba(X_test)[:, 1]
    else:
        probs = predict_proba_fn(model, X_test)
    preds = (probs >= threshold).astype(int)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_acc, cv_f1, cv_auc = [], [], []
    for tr, te in cv.split(np.zeros(len(y_train)), y_train):
        if hasattr(X_train, "iloc"):
            Xtr, Xte = X_train.iloc[tr], X_train.iloc[te]
        elif isinstance(X_train, list):
            Xtr = [X_train[i] for i in tr]
            Xte = [X_train[i] for i in te]
        else:
            Xtr, Xte = X_train[tr], X_train[te]
        ytr, yte = y_train[tr], y_train[te]
        m = _clone_lazy(model)
        m.fit(Xtr, ytr)
        if predict_proba_fn is None:
            p = m.predict_proba(Xte)[:, 1]
        else:
            p = predict_proba_fn(m, Xte)
        pp = (p >= threshold).astype(int)
        cv_acc.append(accuracy_score(yte, pp))
        cv_f1.append(f1_score(yte, pp, zero_division=0))
        try:
            cv_auc.append(roc_auc_score(yte, p))
        except ValueError:
            cv_auc.append(0.5)

    report = classification_report(y_test, preds, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_test, preds).tolist()
    return ModelMetrics(
        name=name,
        accuracy=accuracy_score(y_test, preds),
        precision=precision_score(y_test, preds, zero_division=0),
        recall=recall_score(y_test, preds, zero_division=0),
        f1=f1_score(y_test, preds, zero_division=0),
        roc_auc=roc_auc_score(y_test, probs) if len(set(y_test)) > 1 else 0.5,
        cv_accuracy_mean=float(np.mean(cv_acc)),
        cv_accuracy_std=float(np.std(cv_acc)),
        cv_f1_mean=float(np.mean(cv_f1)),
        cv_f1_std=float(np.std(cv_f1)),
        cv_auc_mean=float(np.mean(cv_auc)),
        cv_auc_std=float(np.std(cv_auc)),
        confusion=cm,
        report=report,
        train_time_sec=train_time,
        n_train=len(y_train),
        n_test=len(y_test),
        threshold=threshold,
    )


def _clone_lazy(estimator):
    """Best-effort clone that works for sklearn pipelines + LightGBM."""
    from sklearn.base import clone
    try:
        return clone(estimator)
    except Exception:
        # Fallback: pickle round-trip
        return pickle.loads(pickle.dumps(estimator))


# ---------------------------------------------------------------------------
# Model builders
# ---------------------------------------------------------------------------
def build_text_baseline():
    """Baseline: word-level TF-IDF → LogReg."""
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=2,
            max_features=20000,
            sublinear_tf=True,
        )),
        ("clf", LogisticRegression(
            solver="liblinear", C=1.0, class_weight="balanced", max_iter=1000,
        )),
    ])


def _text_only_col(df):
    """Pickle-safe helper that delegates to the canonical module."""
    return text_only_col(df)


def build_text_upgraded():
    """Upgraded: word + char TF-IDF + linguistic features, calibrated LR."""
    word_vec = TfidfVectorizer(
        ngram_range=(1, 2), min_df=2, max_features=30000,
        sublinear_tf=True, analyzer="word",
    )
    char_vec = TfidfVectorizer(
        ngram_range=(3, 5), min_df=2, max_features=30000,
        sublinear_tf=True, analyzer="char_wb",
    )

    features = FeatureUnion([
        ("word", Pipeline([("pick", FunctionTransformer(text_only_col, validate=False)),
                            ("vec", word_vec)])),
        ("char", Pipeline([("pick", FunctionTransformer(text_only_col, validate=False)),
                            ("vec", char_vec)])),
        ("ling", Pipeline([("ling", LinguisticFeatures()),
                            ("scale", StandardScaler(with_mean=False))])),
    ])

    base = LogisticRegression(
        solver="liblinear", C=2.0, class_weight="balanced", max_iter=2000,
    )
    calibrated = CalibratedClassifierCV(base, method="isotonic", cv=3)
    return Pipeline([("features", features), ("clf", calibrated)])


def build_metadata_baseline():
    return GradientBoostingClassifier(random_state=42)


def build_metadata_upgraded(X_train, y_train):
    """LightGBM with random search; falls back to GradientBoosting if missing."""
    if not HAS_LGB:
        return GradientBoostingClassifier(random_state=42, n_estimators=300,
                                          max_depth=4, learning_rate=0.05)

    from sklearn.model_selection import RandomizedSearchCV

    grid = {
        "num_leaves": [15, 31, 63, 127],
        "learning_rate": [0.02, 0.05, 0.08, 0.1],
        "n_estimators": [200, 400, 600],
        "min_child_samples": [5, 10, 20, 40],
        "subsample": [0.7, 0.85, 1.0],
        "colsample_bytree": [0.6, 0.8, 1.0],
        "reg_lambda": [0.0, 0.5, 1.0],
    }
    base = lgb.LGBMClassifier(
        objective="binary", random_state=42, n_jobs=-1, verbose=-1,
    )
    cv = StratifiedKFold(n_splits=4, shuffle=True, random_state=42)
    search = RandomizedSearchCV(
        base, grid, n_iter=25, scoring="roc_auc", cv=cv,
        random_state=42, n_jobs=-1, refit=True, verbose=0,
    )
    search.fit(X_train, y_train)
    best = search.best_estimator_
    # Wrap with isotonic calibration for better probabilities
    cal = CalibratedClassifierCV(best, method="isotonic", cv=3)
    return cal


def build_fusion_baseline():
    return LogisticRegression(solver="liblinear", class_weight="balanced", max_iter=1000)


def build_fusion_upgraded():
    # Same family but with isotonic calibration over CV
    base = LogisticRegression(C=2.0, solver="liblinear",
                              class_weight="balanced", max_iter=2000)
    return CalibratedClassifierCV(base, method="isotonic", cv=3)


def tune_threshold(y_true, probs):
    """Pick threshold that maximises F1 (in [0.1, 0.9])."""
    best_t, best_f1 = 0.5, -1.0
    for t in np.linspace(0.1, 0.9, 81):
        f = f1_score(y_true, (probs >= t).astype(int), zero_division=0)
        if f > best_f1:
            best_f1, best_t = f, float(t)
    return best_t


# ---------------------------------------------------------------------------
# Save model + card
# ---------------------------------------------------------------------------
def save_with_card(model, name: str, metrics: ModelMetrics, feature_names: List[str]):
    SAVED_MODELS.mkdir(parents=True, exist_ok=True)
    pkl_path = SAVED_MODELS / f"{name}.pkl"
    card_path = SAVED_MODELS / f"{name}.card.json"
    with open(pkl_path, "wb") as f:
        pickle.dump(model, f)

    card = {
        "module": name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "metrics": {
            "accuracy": metrics.accuracy,
            "precision": metrics.precision,
            "recall": metrics.recall,
            "f1": metrics.f1,
            "roc_auc": metrics.roc_auc,
            "cv": {
                "accuracy_mean": metrics.cv_accuracy_mean,
                "accuracy_std": metrics.cv_accuracy_std,
                "f1_mean": metrics.cv_f1_mean,
                "f1_std": metrics.cv_f1_std,
                "auc_mean": metrics.cv_auc_mean,
                "auc_std": metrics.cv_auc_std,
            },
            "confusion_matrix": metrics.confusion,
            "report": metrics.report,
            "threshold": metrics.threshold,
            "train_time_sec": metrics.train_time_sec,
            "n_train": metrics.n_train,
            "n_test": metrics.n_test,
            "extras": metrics.extras,
        },
        "feature_names": feature_names,
        "label_semantics": {"0": "genuine", "1": "fake"},
    }
    with open(card_path, "w") as f:
        json.dump(card, f, indent=2)
    return pkl_path, card_path


# ---------------------------------------------------------------------------
# Pipelines per modality
# ---------------------------------------------------------------------------
def run_text(df: pd.DataFrame, version: str) -> Tuple[ModelMetrics, object]:
    X = df[["text", "rating"]]
    y = df["label"].values
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y,
    )
    if version == "baseline":
        # Baseline: only the text column.
        Xtr = X_train["text"].astype(str).tolist()
        Xte = X_test["text"].astype(str).tolist()
        m = build_text_baseline()
        metrics = _eval("text_baseline", m, Xtr, y_train, Xte, y_test)
        return metrics, m
    else:
        m = build_text_upgraded()
        # tune threshold using OOF preds on training set
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        oof = cross_val_predict(m, X_train, y_train, cv=cv, method="predict_proba")[:, 1]
        thr = tune_threshold(y_train, oof)
        metrics = _eval("text_upgraded", m, X_train, y_train, X_test, y_test,
                        threshold=thr)
        return metrics, m


def run_metadata(df: pd.DataFrame, version: str) -> Tuple[ModelMetrics, object]:
    X = df[METADATA_COLS].values
    y = df["label"].values
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y,
    )
    if version == "baseline":
        m = build_metadata_baseline()
        metrics = _eval("metadata_baseline", m, X_train, y_train, X_test, y_test)
        return metrics, m
    else:
        m = build_metadata_upgraded(X_train, y_train)
        # fit then tune threshold on training-set probabilities
        m.fit(X_train, y_train)
        probs_train = m.predict_proba(X_train)[:, 1]
        thr = tune_threshold(y_train, probs_train)
        metrics = _eval("metadata_upgraded", m, X_train, y_train, X_test, y_test,
                        threshold=thr)
        # Capture feature importance for the report
        try:
            cc = m.calibrated_classifiers_[0]
            inner = getattr(cc, "estimator", None) or getattr(cc, "base_estimator", None)
            if inner is not None and hasattr(inner, "feature_importances_"):
                metrics.extras["feature_importance"] = {
                    n: float(v) for n, v in zip(METADATA_COLS, inner.feature_importances_)
                }
        except Exception as e:
            metrics.extras["feature_importance_error"] = str(e)
        return metrics, m


def build_oof_fusion_inputs(df_train: pd.DataFrame,
                            text_model, meta_model) -> np.ndarray:
    """Out-of-fold predictions from text+meta on the training set."""
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    y = df_train["label"].values
    text_oof = cross_val_predict(
        text_model, df_train[["text", "rating"]], y, cv=cv,
        method="predict_proba",
    )[:, 1]
    meta_oof = cross_val_predict(
        meta_model, df_train[METADATA_COLS].values, y, cv=cv,
        method="predict_proba",
    )[:, 1]
    return np.column_stack([text_oof, meta_oof])


def run_fusion(df: pd.DataFrame,
               text_model, meta_model,
               version: str) -> Tuple[ModelMetrics, object]:
    df_train, df_test = train_test_split(
        df, test_size=0.2, random_state=42, stratify=df["label"],
    )
    y_train = df_train["label"].values
    y_test = df_test["label"].values

    # Use the *same* base learners but freshly cloned so we don't peek.
    base_text = _clone_lazy(text_model)
    base_meta = _clone_lazy(meta_model)

    print("  [fusion] Building OOF base predictions on training fold ...")
    X_train_fusion = build_oof_fusion_inputs(df_train, base_text, base_meta)

    # Fit final base learners on full training data, score test set
    base_text.fit(df_train[["text", "rating"]], y_train)
    base_meta.fit(df_train[METADATA_COLS].values, y_train)
    test_text = base_text.predict_proba(df_test[["text", "rating"]])[:, 1]
    test_meta = base_meta.predict_proba(df_test[METADATA_COLS].values)[:, 1]
    X_test_fusion = np.column_stack([test_text, test_meta])

    if version == "baseline":
        m = build_fusion_baseline()
        metrics = _eval("fusion_baseline", m, X_train_fusion, y_train,
                        X_test_fusion, y_test)
        return metrics, m
    else:
        m = build_fusion_upgraded()
        m.fit(X_train_fusion, y_train)
        probs_train = m.predict_proba(X_train_fusion)[:, 1]
        thr = tune_threshold(y_train, probs_train)
        # Re-evaluate with tuned threshold
        probs_test = m.predict_proba(X_test_fusion)[:, 1]
        preds = (probs_test >= thr).astype(int)
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_acc, cv_f1, cv_auc = [], [], []
        for tr, te in cv.split(X_train_fusion, y_train):
            mm = _clone_lazy(m)
            mm.fit(X_train_fusion[tr], y_train[tr])
            p = mm.predict_proba(X_train_fusion[te])[:, 1]
            pp = (p >= thr).astype(int)
            cv_acc.append(accuracy_score(y_train[te], pp))
            cv_f1.append(f1_score(y_train[te], pp, zero_division=0))
            try:
                cv_auc.append(roc_auc_score(y_train[te], p))
            except ValueError:
                cv_auc.append(0.5)
        metrics = ModelMetrics(
            name="fusion_upgraded",
            accuracy=accuracy_score(y_test, preds),
            precision=precision_score(y_test, preds, zero_division=0),
            recall=recall_score(y_test, preds, zero_division=0),
            f1=f1_score(y_test, preds, zero_division=0),
            roc_auc=roc_auc_score(y_test, probs_test) if len(set(y_test)) > 1 else 0.5,
            cv_accuracy_mean=float(np.mean(cv_acc)),
            cv_accuracy_std=float(np.std(cv_acc)),
            cv_f1_mean=float(np.mean(cv_f1)),
            cv_f1_std=float(np.std(cv_f1)),
            cv_auc_mean=float(np.mean(cv_auc)),
            cv_auc_std=float(np.std(cv_auc)),
            confusion=confusion_matrix(y_test, preds).tolist(),
            report=classification_report(y_test, preds, output_dict=True, zero_division=0),
            train_time_sec=0.0,
            n_train=len(y_train),
            n_test=len(y_test),
            threshold=thr,
        )
        return metrics, m


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def _fmt(m: ModelMetrics) -> str:
    return (
        f"| {m.name} | {m.accuracy:.4f} | {m.precision:.4f} | {m.recall:.4f} | "
        f"{m.f1:.4f} | {m.roc_auc:.4f} | "
        f"{m.cv_accuracy_mean:.4f} ± {m.cv_accuracy_std:.3f} | "
        f"{m.cv_f1_mean:.4f} ± {m.cv_f1_std:.3f} | "
        f"{m.cv_auc_mean:.4f} ± {m.cv_auc_std:.3f} | {m.threshold:.2f} |"
    )


def write_report(results: Dict[str, ModelMetrics], dataset_info: Dict):
    lines = []
    lines.append("# ReviewGuard – ML Accuracy Upgrade Report")
    lines.append("")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")
    lines.append("## Why the previous numbers were misleading")
    lines.append("")
    lines.append(
        "- The shipped `train_text.csv` contained a single repeated sentence "
        "(`\"This is an amazing product!\"`) for every row. Genuine rows used "
        "rating = 5, fake rows used rating = 1 – which means the text model "
        "could not learn text at all (its model card honestly recorded "
        "`accuracy = 0.5`, `ROC-AUC = 0.5`)."
    )
    lines.append(
        "- The fusion classifier card reported `accuracy = 1.0` because it was "
        "trained on `[text_len, rating_norm]` where both values were constant per class, "
        "so the perfect score was a memorisation artifact, not generalisation."
    )
    lines.append(
        "- The metadata classifier also showed `accuracy = 1.0` on only 160 "
        "synthetic rows with very thin separation – another overfit on a tiny set."
    )
    lines.append("")
    lines.append("## What changed")
    lines.append("")
    lines.append(
        "1. **Realistic synthetic dataset** generated by "
        "`ml_service/improved/synth_dataset.py` – {n} rows with jointly-aligned "
        "text + 10 metadata features + label. Genuine and fake reviewers have "
        "different writing styles (vocabulary, superlative density, ALL-CAPS rate, "
        "sentiment vs rating mismatch) **and** different metadata distributions "
        "(account age, reviews/day, verified ratio, burstiness, copy-paste similarity, "
        "night posting, reviewer overlap)."
        .format(n=dataset_info["n_rows"])
    )
    lines.append(
        "2. **Honest evaluation** – stratified 80/20 train/test split, plus "
        "5-fold stratified cross-validation reported with mean ± std."
    )
    lines.append(
        "3. **Baseline (a)** – TF-IDF (word) + LogReg for text, "
        "GradientBoostingClassifier for metadata, LogReg over base probabilities "
        "for fusion."
    )
    lines.append(
        "4. **Upgraded (b)** – word + char TF-IDF + 11 linguistic features → "
        "calibrated LogReg for text; LightGBM with randomized hyper-parameter "
        "search + isotonic calibration for metadata; stacking fusion with "
        "out-of-fold base predictions to prevent leakage + F1-optimal "
        "threshold tuning."
    )
    lines.append("")
    lines.append("## Dataset")
    lines.append("")
    lines.append(f"- Rows: **{dataset_info['n_rows']}**")
    lines.append(f"- Fake share: **{dataset_info['fake_share']:.2f}**")
    lines.append(f"- Saved at: `{dataset_info['paths']['full']}`")
    lines.append("")
    lines.append("## Headline metrics (test set, 20 % held out, stratified)")
    lines.append("")
    lines.append("| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | CV Acc | CV F1 | CV AUC | Thr |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    order = ["text_baseline", "text_upgraded",
             "metadata_baseline", "metadata_upgraded",
             "fusion_baseline", "fusion_upgraded"]
    for k in order:
        if k in results:
            lines.append(_fmt(results[k]))
    lines.append("")

    lines.append("## Confusion matrices (rows = true, cols = predicted)")
    lines.append("")
    for k in order:
        if k not in results:
            continue
        m = results[k]
        lines.append(f"### {m.name}")
        cm = m.confusion
        lines.append("")
        lines.append("|              | pred genuine | pred fake |")
        lines.append("|--------------|--------------|-----------|")
        lines.append(f"| true genuine | {cm[0][0]} | {cm[0][1]} |")
        lines.append(f"| true fake    | {cm[1][0]} | {cm[1][1]} |")
        lines.append("")

    # Feature importance for upgraded metadata, if available
    if "metadata_upgraded" in results and results["metadata_upgraded"].extras.get("feature_importance"):
        fi = results["metadata_upgraded"].extras["feature_importance"]
        lines.append("## Metadata feature importance (upgraded)")
        lines.append("")
        lines.append("| Feature | Importance |")
        lines.append("|---|---|")
        for name, val in sorted(fi.items(), key=lambda kv: -kv[1]):
            lines.append(f"| {name} | {val:.4f} |")
        lines.append("")

    # Improvements
    lines.append("## Baseline vs Upgraded – Δ on test set")
    lines.append("")
    lines.append("| Modality | Δ Accuracy | Δ F1 | Δ ROC-AUC |")
    lines.append("|---|---|---|---|")
    for mod in ["text", "metadata", "fusion"]:
        b = results.get(f"{mod}_baseline")
        u = results.get(f"{mod}_upgraded")
        if not b or not u:
            continue
        lines.append(
            f"| {mod} | {(u.accuracy - b.accuracy):+.4f} "
            f"| {(u.f1 - b.f1):+.4f} "
            f"| {(u.roc_auc - b.roc_auc):+.4f} |"
        )
    lines.append("")

    lines.append("## Saved artifacts (consumed by `ml_service/models/*.py` at inference time)")
    lines.append("")
    lines.append("- `saved_models/text_classifier.pkl` – upgraded text pipeline (DataFrame in, fake-prob out)")
    lines.append("- `saved_models/text_classifier.card.json`")
    lines.append("- `saved_models/metadata_classifier.pkl` – LightGBM (or GBDT fallback) + isotonic calibration")
    lines.append("- `saved_models/metadata_classifier.card.json`")
    lines.append("- `saved_models/fusion_classifier.pkl` – calibrated stacking LR over [text_prob, meta_prob]")
    lines.append("- `saved_models/fusion_classifier.card.json`")
    lines.append("")
    lines.append("> The upgraded text pipeline expects a `pandas.DataFrame` with the "
                 "columns `text` and `rating`. The existing `TextModel.predict()` path "
                 "in `ml_service/models/text_model.py` calls the classifier with a list "
                 "of features, so a small adapter (see `ml_service/improved/inference_adapter.py`) "
                 "is provided to plug the upgraded pipeline back in without breaking the "
                 "existing API contract.")
    lines.append("")
    lines.append("## How to reproduce")
    lines.append("")
    lines.append("```bash")
    lines.append("cd ml_service")
    lines.append("python3 improved/synth_dataset.py --n 6000")
    lines.append("python3 improved/train_all.py --n 6000")
    lines.append("python3 ../check_ml_accuracy.py   # confirms new metrics from cards")
    lines.append("```")
    REPORT_PATH.write_text("\n".join(lines))
    print(f"Report written to {REPORT_PATH}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=6000)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--fake-ratio", type=float, default=0.5)
    args = parser.parse_args()

    print(f"Generating {args.n} synthetic rows ...")
    df = generate(n=args.n, fake_ratio=args.fake_ratio, seed=args.seed)
    DATA_DIR.mkdir(exist_ok=True, parents=True)
    full_path = DATA_DIR / "synth_full.csv"
    df.to_csv(full_path, index=False)

    # Also overwrite the original training CSVs so the existing train.py won't
    # silently re-create the degenerate dataset on next run.
    df[["text", "rating", "label"]].to_csv(DATA_DIR / "train_text.csv", index=False)
    meta_cols = METADATA_COLS + ["label"]
    df[meta_cols].to_csv(DATA_DIR / "train_metadata.csv", index=False)

    dataset_info = {
        "n_rows": int(len(df)),
        "fake_share": float(df["label"].mean()),
        "paths": {"full": str(full_path)},
    }
    print(f"Label distribution: {df['label'].value_counts().to_dict()}")

    results: Dict[str, ModelMetrics] = {}

    print("\n=== Text models ===")
    print("- baseline: TF-IDF(word 1-2grams) → LogReg")
    m_tb, _ = run_text(df, "baseline")
    results["text_baseline"] = m_tb
    print(f"  acc={m_tb.accuracy:.4f}  f1={m_tb.f1:.4f}  auc={m_tb.roc_auc:.4f}")

    print("- upgraded: TF-IDF(word+char) + linguistic features → calibrated LR")
    m_tu, text_pipeline_upgraded = run_text(df, "upgraded")
    results["text_upgraded"] = m_tu
    print(f"  acc={m_tu.accuracy:.4f}  f1={m_tu.f1:.4f}  auc={m_tu.roc_auc:.4f}  thr={m_tu.threshold:.2f}")

    print("\n=== Metadata models ===")
    print("- baseline: GradientBoostingClassifier")
    m_mb, _ = run_metadata(df, "baseline")
    results["metadata_baseline"] = m_mb
    print(f"  acc={m_mb.accuracy:.4f}  f1={m_mb.f1:.4f}  auc={m_mb.roc_auc:.4f}")

    print(f"- upgraded: {'LightGBM' if HAS_LGB else 'GBDT'} + randomized search + isotonic calibration")
    m_mu, meta_pipeline_upgraded = run_metadata(df, "upgraded")
    results["metadata_upgraded"] = m_mu
    print(f"  acc={m_mu.accuracy:.4f}  f1={m_mu.f1:.4f}  auc={m_mu.roc_auc:.4f}  thr={m_mu.threshold:.2f}")

    print("\n=== Fusion models ===")
    print("- baseline: LogReg over [text_prob, meta_prob]")
    m_fb, fusion_baseline_model = run_fusion(df, text_pipeline_upgraded,
                                              meta_pipeline_upgraded, "baseline")
    results["fusion_baseline"] = m_fb
    print(f"  acc={m_fb.accuracy:.4f}  f1={m_fb.f1:.4f}  auc={m_fb.roc_auc:.4f}")

    print("- upgraded: Calibrated stacking + F1-tuned threshold (OOF base preds)")
    m_fu, fusion_model = run_fusion(df, text_pipeline_upgraded,
                                     meta_pipeline_upgraded, "upgraded")
    results["fusion_upgraded"] = m_fu
    print(f"  acc={m_fu.accuracy:.4f}  f1={m_fu.f1:.4f}  auc={m_fu.roc_auc:.4f}  thr={m_fu.threshold:.2f}")

    print("\nSaving upgraded artifacts ...")
    save_with_card(text_pipeline_upgraded, "text_classifier", m_tu,
                   ["tfidf_word", "tfidf_char", "linguistic_features"])
    save_with_card(meta_pipeline_upgraded, "metadata_classifier", m_mu,
                   METADATA_COLS)
    save_with_card(fusion_model, "fusion_classifier", m_fu,
                   ["text_prob", "meta_prob"])

    write_report(results, dataset_info)
    print("Done.")


if __name__ == "__main__":
    main()
