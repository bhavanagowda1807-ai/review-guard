import argparse, os, numpy as np, pandas as pd, pickle, json
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
from datetime import datetime, timezone

META_COLS = [
    'account_age', 'reviews_per_day', 'verified_purchase_ratio',
    'rating_deviation', 'burstiness', 'helpfulness_ratio',
    'similarity_score', 'sentiment_rating_mismatch',
    'night_review_ratio', 'reviewer_overlap_score',
]

MODEL_DIR = "/app/saved_models"

def save_pkl(obj, name):
    p = os.path.join(MODEL_DIR, name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as f: pickle.dump(obj, f)

def save_card(name, metrics, features):
    p = os.path.join(MODEL_DIR, name)
    card = {
        'created_at': datetime.now(timezone.utc).isoformat(),
        'metrics': metrics,
        'feature_names': features,
        'label_semantics': {'0': 'genuine', '1': 'fake'},
        'new_features': [
            'similarity_score: cosine similarity between user reviews (copy-paste detection)',
            'sentiment_rating_mismatch: divergence between text sentiment and star rating',
            'night_review_ratio: fraction of reviews submitted between 1am-5am (bot signal)',
            'reviewer_overlap_score: co-occurrence with known fake reviewers on same products',
        ]
    }
    with open(p, 'w') as f: json.dump(card, f, indent=2)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--metadata-data', required=True)
    ap.add_argument('--samples', type=int, default=800)
    args = ap.parse_args()

    df = pd.read_csv(args.metadata_data).head(args.samples)

    # Handle missing new columns gracefully (fill with neutral 0.5)
    for col in META_COLS:
        if col not in df.columns:
            print(f"  Warning: column '{col}' not found, filling with 0.5")
            df[col] = 0.5

    X = df[META_COLS].values
    y = df['label'].values if 'label' in df.columns else np.zeros(len(df))

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)

    clf = XGBClassifier(
        use_label_encoder=False,
        eval_metric='logloss',
        random_state=42,
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
    )
    clf.fit(Xtr, ytr)

    preds = clf.predict(Xte)
    probs = clf.predict_proba(Xte)[:, 1]
    m = {
        'accuracy': float(accuracy_score(yte, preds)),
        'roc_auc':  float(roc_auc_score(yte, probs)),
        'report':   classification_report(yte, preds, output_dict=True),
        'feature_importance': dict(zip(META_COLS, clf.feature_importances_.tolist())),
    }
    save_pkl(clf, 'metadata_classifier.pkl')
    save_card('metadata_classifier.card.json', m, META_COLS)
    print("Metadata training complete")
    print(f"  Accuracy: {m['accuracy']:.3f}  ROC-AUC: {m['roc_auc']:.3f}")
    print("  Feature importances:")
    for feat, imp in sorted(zip(META_COLS, clf.feature_importances_), key=lambda x: -x[1]):
        bar = "█" * int(imp * 40)
        print(f"    {feat:<32} {imp:.3f}  {bar}")

if __name__ == '__main__':
    main()
