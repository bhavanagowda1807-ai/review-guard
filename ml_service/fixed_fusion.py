import argparse, os, re, numpy as np, pandas as pd, pickle, json
from datetime import datetime, timezone
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report

# ── same text features as fixed_train.py ─────────────────────────────────────
def text_features(text, rating):
    text = text or ""
    words = re.findall(r'\w+', text)
    n = max(len(words), 1)
    caps   = sum(1 for w in words if w.isupper() and len(w) > 1) / n
    excl   = text.count('!') / max(len(text), 1)
    supers = len(re.findall(
        r'\b(best|worst|amazing|perfect|incredible|fantastic|love|excellent|outstanding|wonderful|superb)\b',
        text, re.I)) / n
    reps   = len(re.findall(r'\b(\w+)\b(?:\W+\1\b)+', text, re.I))
    sents  = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    slens  = [len(re.findall(r'\w+', s)) for s in sents]
    svar   = float(np.var(slens)) if len(slens) > 1 else 0.0
    savg   = float(np.mean(slens)) if slens else 0.0
    r5     = 1.0 if float(rating) == 5.0 else 0.0
    uniq   = len(set(w.lower() for w in words)) / n
    return [caps, excl, supers, reps, svar, savg, r5, uniq, n]

META_COLS = ['account_age','reviews_per_day','verified_purchase_ratio',
             'rating_deviation','burstiness','helpfulness_ratio']

MODEL_DIR = "/app/saved_models"

def load_pkl(name):
    p = os.path.join(MODEL_DIR, name)
    with open(p, 'rb') as f: return pickle.load(f)

def save_pkl(obj, name):
    p = os.path.join(MODEL_DIR, name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as f: pickle.dump(obj, f)

def save_card(name, metrics, features):
    p = os.path.join(MODEL_DIR, name)
    card = {'created_at': datetime.now(timezone.utc).isoformat(),
            'metrics': metrics, 'feature_names': features,
            'label_semantics': {'0': 'genuine', '1': 'fake'}}
    with open(p, 'w') as f: json.dump(card, f, indent=2)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--text-data',     required=True)
    ap.add_argument('--metadata-data', required=True)
    ap.add_argument('--samples', type=int, default=800)
    args = ap.parse_args()

    tdf = pd.read_csv(args.text_data).head(args.samples)
    mdf = pd.read_csv(args.metadata_data).head(args.samples)
    n   = min(len(tdf), len(mdf))

    text_clf = load_pkl('text_classifier.pkl')
    meta_clf = load_pkl('metadata_classifier.pkl')

    X_rows, y = [], []
    for i in range(n):
        tr = tdf.iloc[i]
        mr = mdf.iloc[i]

        tf = text_features(str(tr['text']), tr.get('rating', 3))
        t_prob = float(text_clf.predict_proba([[tf[0]]])[0][1])

        mf = [mr[c] for c in META_COLS]
        m_prob = float(meta_clf.predict_proba([mf])[0][1])

        X_rows.append([t_prob, m_prob])
        y.append(int(tr['label']))

    X = np.array(X_rows)
    y = np.array(y)

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
    clf = LogisticRegression(solver='liblinear')
    clf.fit(Xtr, ytr)

    preds = clf.predict(Xte)
    probs = clf.predict_proba(Xte)[:, 1]
    m = {
        'accuracy': float(accuracy_score(yte, preds)),
        'roc_auc':  float(roc_auc_score(yte, probs)),
        'report':   classification_report(yte, preds, output_dict=True)
    }
    save_pkl(clf, 'fusion_classifier.pkl')
    save_card('fusion_classifier.card.json', m, ['text_prob', 'meta_prob'])
    print("Fusion training complete", {k: v for k, v in m.items() if k != 'report'})

if __name__ == '__main__':
    main()
