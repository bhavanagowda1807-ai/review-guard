"""Evaluation script — text and metadata only."""
import argparse
import os
import numpy as np
from sklearn.metrics import classification_report, roc_auc_score
from models.text_model import TextModel
from models.metadata_model import MetadataModel
from models.fusion_model import FusionModel
from train.data import load_text_dataset, load_metadata_dataset
from train.utils import load_model, compute_metrics

MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'saved_models')


def evaluate_text(args):
    df = load_text_dataset(args.text_data, n_samples=args.samples)
    model = TextModel()
    scores, labels = [], []
    for _, row in df.iterrows():
        out = model.predict(str(row.get('text', '')), rating=float(row.get('rating', 0)))
        scores.append(out['score'])
        labels.append(int(row.get('label', 0)))
    preds = [1 if s < 0.5 else 0 for s in scores]
    metrics = compute_metrics(np.array(labels), np.array(preds), np.array(scores))
    print('Text evaluation:', metrics)
    return metrics


def evaluate_metadata(args):
    df = load_metadata_dataset(args.metadata_data, n_samples=args.samples)
    model = MetadataModel()
    feature_cols = ['account_age', 'reviews_per_day', 'verified_purchase_ratio',
                    'rating_deviation', 'burstiness', 'helpfulness_ratio']
    scores, labels = [], []
    for _, row in df.iterrows():
        out = model.predict(row.to_dict())
        scores.append(out['score'])
        labels.append(int(row.get('label', 0)))
    preds = [1 if s < 0.5 else 0 for s in scores]
    metrics = compute_metrics(np.array(labels), np.array(preds), np.array(scores))
    print('Metadata evaluation:', metrics)
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--module', choices=['text', 'metadata'], default='text')
    parser.add_argument('--text-data', type=str, default=None)
    parser.add_argument('--metadata-data', type=str, default=None)
    parser.add_argument('--samples', type=int, default=200)
    args = parser.parse_args()

    if args.module == 'text':
        evaluate_text(args)
    else:
        evaluate_metadata(args)


if __name__ == '__main__':
    main()
