import argparse, os, re, numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
import pickle, json
from datetime import datetime, timezone

# ── feature extraction (bypasses TextModel.score_from_features entirely) ──────
def extract_text_features(text: str, rating: float) -> list:
    text = text or ""
    words = re.findall(r'\w+', text)
    total_words = max(len(words), 1)

    caps_words   = sum(1 for w in words if w.isupper() and len(w) > 1)
    caps_ratio   = caps_words / total_words

    excl_count   = text.count('!')
    excl_ratio   = excl_count / max(len(text), 1)

    superlatives = len(re.findall(
        r'\b(best|worst|amazing|perfect|incredible|fantastic|love|excellent|outstanding|wonderful|superb)\b',
        text, re.I))
    super_ratio  = superlatives / total_words

    # repeated consecutive words: "LOVE LOVE LOVE" → high score
    rep_count    = len(re.findall(r'\b(\w+)\b(?:\W+\1\b)+', text, re.I))

    # sentence variance (genuine reviews have varied sentence lengths)
    sentences    = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    sent_lengths = [len(re.findall(r'\w+', s)) for s in sentences]
    sent_var     = float(np.var(sent_lengths)) if len(sent_lengths) > 1 else 0.0

    # avg sentence length (fake = short repeated bursts)
    avg_sent_len = np.mean(sent_lengths) if sent_lengths else 0.0

    # rating signal: fake always = 5
    rating_is_5  = 1.0 if float(rating) == 5.0 else 0.0

    # unique word ratio (fake = low due to repetition)
    unique_ratio = len(set(w.lower() for w in words)) / total_words

    return [
        caps_ratio, excl_ratio, super_ratio, rep_count,
        sent_var, avg_sent_len, rating_is_5, unique_ratio,
        total_words
    ]

FEATURE_NAMES = ['caps_ratio']

MODEL_DIR = "/app/saved_models"

def save(model, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f: pickle.dump(model, f)

def save_card(path, metrics, features):
    card = {'created_at': datetime.now(timezone.utc).isoformat(),
            'metrics': metrics, 'feature_names': features,
            'label_semantics': {'0': 'genuine', '1': 'fake'}}
    with open(path, 'w') as f: json.dump(card, f, indent=2)

def metrics(y_true, y_pred, y_prob):
    return {
        'accuracy':  float(accuracy_score(y_true, y_pred)),
        'roc_auc':   float(roc_auc_score(y_true, y_prob)),
        'report':    classification_report(y_true, y_pred, output_dict=True)
    }

def train_text(csv_path, n):
    import pandas as pd
    df = pd.read_csv(csv_path).head(n)
    X = np.array([extract_text_features(r['text'], r.get('rating', 3))[0:1] for _, r in df.iterrows()])
    y = df['label'].values
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(Xtr, ytr)
    preds = clf.predict(Xte)
    probs = clf.predict_proba(Xte)[:, 1]
    m = metrics(yte, preds, probs)
    pkl  = os.path.join(MODEL_DIR, 'text_classifier.pkl')
    card = pkl.replace('.pkl', '.card.json')
    print(f'Saving to {pkl}')
    save(clf, pkl)
    print(f'Saved PKL, now saving card to {card}')
    save_card(card, m, FEATURE_NAMES)
    print(f'Card saved')
    print("Text training complete", {k: v for k, v in m.items() if k != 'report'})
    return m

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--text-data', required=True)
    ap.add_argument('--samples', type=int, default=800)
    args = ap.parse_args()
    train_text(args.text_data, args.samples)
