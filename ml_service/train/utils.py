import os
import json
import pickle
from datetime import datetime, timezone
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report


def save_model(model, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        pickle.dump(model, f)


def load_model(path):
    with open(path, 'rb') as f:
        return pickle.load(f)


def save_model_card(path, module, metrics, feature_names=None, label_semantics=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    card = {
        'module': module,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'metrics': metrics,
        'feature_names': feature_names or [],
        'label_semantics': label_semantics or {'0': 'genuine', '1': 'fake'},
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(card, f, indent=2)
    return card


def compute_metrics(y_true, y_pred, y_score=None):
    metrics = {
        'accuracy': float(accuracy_score(y_true, y_pred)),
    }
    if y_score is not None:
        try:
            metrics['roc_auc'] = float(roc_auc_score(y_true, y_score))
        except Exception:
            metrics['roc_auc'] = 0.0
    metrics['report'] = classification_report(y_true, y_pred, output_dict=True)
    return metrics
