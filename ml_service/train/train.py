import argparse
import os
import sys
import random
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

# Add app root to path so imports work from anywhere
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

has_mlflow = False
try:
    import mlflow, mlflow.sklearn, mlflow.xgboost
    from mlflow import set_tracking_uri, start_run, log_params, log_metrics
    has_mlflow = True
except Exception:
    mlflow = None
    def set_tracking_uri(uri): return None
    def start_run(*a, **kw):
        class _D:
            def __enter__(self): return None
            def __exit__(self, *a): return False
        return _D()
    def log_params(p): return None
    def log_metrics(m): return None

from models.text_model import TextModel
from models.metadata_model import MetadataModel
from models.fusion_model import FusionModel
from train.data import load_text_dataset, load_metadata_dataset, load_fusion_dataset
from train.utils import save_model, save_model_card, compute_metrics

MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'saved_models')


def save_and_track_model(model, path, artifact_name, args, metrics=None, feature_names=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    save_model(model, path)
    card_path = path.replace('.pkl', '.card.json')
    save_model_card(card_path, artifact_name, metrics or {}, feature_names or [])
    if not args.mlflow:
        return
    if isinstance(model, XGBClassifier):
        mlflow.xgboost.log_model(model, artifact_path=artifact_name)
    else:
        mlflow.sklearn.log_model(model, artifact_path=artifact_name)
    mlflow.log_artifact(path, artifact_path=artifact_name)
    mlflow.log_artifact(card_path, artifact_path=artifact_name)


def setup_mlflow(uri: str):
    try:
        if uri:
            set_tracking_uri(uri)
        if has_mlflow:
            mlflow.set_experiment('fake_review_detection')
    except Exception:
        pass


def train_text(args):
    print('Loading text dataset...')
    df = load_text_dataset(args.text_data, n_samples=args.samples)
    model = TextModel()
    features, labels = [], []
    for _, row in df.iterrows():
        out = model.predict(str(row.get('text', '')), rating=float(row.get('rating', 0)))
        features.append([out['score']])
        labels.append(int(row.get('label', 0)))
    X, y = np.array(features), np.array(labels)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    clf = LogisticRegression(solver='liblinear')
    clf.fit(X_train, y_train)
    preds = clf.predict(X_test)
    probs = clf.predict_proba(X_test)[:, 1]
    metrics = compute_metrics(y_test, preds, probs)
    save_and_track_model(clf, os.path.join(MODEL_DIR, 'text_classifier.pkl'),
                         'text_classifier', args, metrics, ['linguistic_score'])
    print('Text training complete', metrics)
    return metrics


def train_metadata(args):
    print('Loading metadata dataset...')
    df = load_metadata_dataset(args.metadata_data, n_samples=args.samples)
    feature_cols = ['account_age', 'reviews_per_day', 'verified_purchase_ratio',
                    'rating_deviation', 'burstiness', 'helpfulness_ratio']
    X = df[feature_cols].values
    y = df['label'].values
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    clf = XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)
    clf.fit(X_train, y_train)
    preds = clf.predict(X_test)
    probs = clf.predict_proba(X_test)[:, 1]
    metrics = compute_metrics(y_test, preds, probs)
    save_and_track_model(clf, os.path.join(MODEL_DIR, 'metadata_classifier.pkl'),
                         'metadata_classifier', args, metrics, feature_cols)
    print('Metadata training complete', metrics)
    return metrics


def train_fusion(args):
    print('Building fusion dataset...')
    text_df = load_text_dataset(args.text_data, n_samples=args.samples)
    meta_df = load_metadata_dataset(args.metadata_data, n_samples=args.samples)
    min_rows = min(len(text_df), len(meta_df))

    text_model = TextModel()
    meta_model = MetadataModel()
    text_scores, meta_scores, labels = [], [], []

    for i in range(min_rows):
        text_row = text_df.iloc[i]
        meta_row = meta_df.iloc[i]
        text_out = text_model.predict(str(text_row['text']), rating=float(text_row['rating']))
        meta_out = meta_model.predict(meta_row.to_dict())
        text_scores.append(text_out['score'])
        meta_scores.append(meta_out['score'])
        labels.append(int(text_row.get('label', 0)))

    df = load_fusion_dataset(text_scores, meta_scores, labels)
    X = df[['text_score', 'meta_score']].values
    y = df['label'].values
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    clf = LogisticRegression(solver='liblinear')
    clf.fit(X_train, y_train)
    preds = clf.predict(X_test)
    probs = clf.predict_proba(X_test)[:, 1]
    metrics = compute_metrics(y_test, preds, probs)
    save_and_track_model(clf, os.path.join(MODEL_DIR, 'fusion_classifier.pkl'),
                         'fusion_classifier', args, metrics, ['text_score', 'meta_score'])
    print('Fusion training complete', metrics)
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--module', choices=['text', 'metadata', 'fusion'], default='fusion')
    parser.add_argument('--text-data', type=str, default=None)
    parser.add_argument('--metadata-data', type=str, default=None)
    parser.add_argument('--samples', type=int, default=200)
    parser.add_argument('--mlflow', action='store_true')
    parser.add_argument('--mlflow-uri', type=str, default=None)
    args = parser.parse_args()

    if args.mlflow:
        setup_mlflow(args.mlflow_uri or os.getenv('MLFLOW_TRACKING_URI') or 'http://localhost:5000')

    if args.module == 'text':
        metrics = train_text(args)
    elif args.module == 'metadata':
        metrics = train_metadata(args)
    else:
        metrics = train_fusion(args)

    if args.mlflow:
        with start_run():
            log_params({'module': args.module, 'samples': args.samples})
            log_metrics({k: v for k, v in metrics.items() if k != 'report'})

    print('Done. Metrics:', metrics)


if __name__ == '__main__':
    main()
