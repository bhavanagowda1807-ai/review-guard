import random
from pathlib import Path
from typing import Optional
import pandas as pd

TEXT_LABELS = [
    ('This product is amazing and works perfectly', 0),
    ('Worst purchase ever, do not buy', 1),
    ('Great value for the price and high quality', 0),
    ('Completely fake product and terrible service', 1),
    ('I love it, exactly as described', 0),
    ('This is a scam and did not arrive', 1),
]

METADATA_HEADERS = [
    'account_age', 'reviews_per_day', 'verified_purchase_ratio',
    'rating_deviation', 'burstiness', 'helpfulness_ratio',
]


def _require_columns(df, columns, dataset_name):
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"{dataset_name} is missing required columns: {', '.join(missing)}")
    return df


def _normalize_label(value):
    if isinstance(value, str):
        cleaned = value.strip().lower()
        if cleaned in {'fake', 'deceptive', 'spam', '1'}:
            return 1
        if cleaned in {'genuine', 'truthful', 'real', '0'}:
            return 0
    return int(value)


def load_text_dataset(path: Optional[str] = None, n_samples: int = 200):
    if path and Path(path).exists():
        df = pd.read_csv(path)
        aliases = {'review': 'text', 'review_text': 'text',
                   'Comment': 'text', 'comment': 'text',
                   'stars': 'rating', 'Rating': 'rating',
                   'class': 'label', 'is_fake': 'label', 'Label': 'label'}
        df = df.rename(columns={s: t for s, t in aliases.items() if s in df.columns})
        _require_columns(df, ['text', 'label'], 'text dataset')
        if 'rating' not in df.columns:
            df['rating'] = 3
        df['label'] = df['label'].apply(_normalize_label)
        return df[['text', 'rating', 'label']].dropna(subset=['text', 'label'])
    rows = []
    for _ in range(n_samples):
        text, label = random.choice(TEXT_LABELS)
        if random.random() > 0.6:
            text = text + ' ' + random.choice(['excellent', 'best', 'terrible', 'awful'])
        rows.append({'text': text, 'rating': random.randint(1, 5), 'label': label})
    return pd.DataFrame(rows)


def load_metadata_dataset(path: Optional[str] = None, n_samples: int = 200):
    if path and Path(path).exists():
        df = pd.read_csv(path)
        _require_columns(df, METADATA_HEADERS + ['label'], 'metadata dataset')
        df['label'] = df['label'].apply(_normalize_label)
        return df[METADATA_HEADERS + ['label']]
    rows = []
    for _ in range(n_samples):
        account_age = random.uniform(0, 730)
        reviews_per_day = random.uniform(0, 5)
        verified_purchase_ratio = random.random()
        rating_deviation = random.uniform(0, 2)
        burstiness = random.uniform(0, 5)
        helpfulness_ratio = random.random()
        label = 1 if verified_purchase_ratio < 0.4 and burstiness > 3 else 0
        rows.append({
            'account_age': account_age, 'reviews_per_day': reviews_per_day,
            'verified_purchase_ratio': verified_purchase_ratio,
            'rating_deviation': rating_deviation, 'burstiness': burstiness,
            'helpfulness_ratio': helpfulness_ratio, 'label': label,
        })
    return pd.DataFrame(rows)


def load_fusion_dataset(text_scores, meta_scores, labels):
    """Build fusion training dataframe from text + metadata scores."""
    return pd.DataFrame({
        'text_score': text_scores,
        'meta_score': meta_scores,
        'label': labels,
    })
