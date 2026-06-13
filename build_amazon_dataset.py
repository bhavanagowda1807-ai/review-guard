"""
build_amazon_dataset.py
========================
Downloads real Amazon review data and computes all 13 metadata features
needed by your ReviewGuard metadata + text classifier.

Usage:
    pip install datasets vaderSentiment scikit-learn pandas numpy
    python build_amazon_dataset.py

Output:
    amazon_reviews_computed.csv  — ready to upload to ReviewGuard admin dashboard

Columns produced:
    product, review_text, rating,
    account_age, reviews_per_day, verified_purchase_ratio,
    rating_deviation, burstiness, helpfulness_ratio,
    similarity_score, sentiment_rating_mismatch,
    night_review_ratio, reviewer_overlap_score
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import math
import warnings
warnings.filterwarnings("ignore")

# ── Config ────────────────────────────────────────────────────────────────────
CATEGORY        = "All_Beauty"       # Amazon category to download
MAX_REVIEWS     = 2000               # total reviews to process (keep low for speed)
MIN_REVIEWS_PER_USER = 2             # need at least 2 reviews to compute behavioral features
OUTPUT_FILE     = "amazon_reviews_computed.csv"

print(f"\n{'='*60}")
print(f"  ReviewGuard — Amazon Dataset Builder")
print(f"  Category : {CATEGORY}")
print(f"  Max rows : {MAX_REVIEWS}")
print(f"{'='*60}\n")


# ── Step 1: Download from HuggingFace ────────────────────────────────────────
print("[1/6] Downloading Amazon reviews from HuggingFace...")
try:
    from datasets import load_dataset
    ds = load_dataset(
        "McAuley-Lab/Amazon-Reviews-2023",
        f"raw_review_{CATEGORY}",
        split="full",
        # trust_remote_code removed (deprecated in newer datasets versions)
        streaming=True,
    )
    rows = []
    for item in ds:
        rows.append(item)
        if len(rows) >= MAX_REVIEWS:
            break
    df_raw = pd.DataFrame(rows)
    print(f"  Downloaded {len(df_raw)} reviews")
    print(f"  Columns: {list(df_raw.columns)}\n")
except Exception as e:
    print(f"  ERROR downloading: {e}")
    print("  Falling back to sample data for testing...\n")
    # Fallback: create a minimal sample so the script still runs
    import random
    random.seed(42)
    sample_texts = [
        "Great product, works perfectly.", "Terrible quality, broke after a week.",
        "Decent for the price.", "Amazing! Best purchase ever!!!",
        "Not as described, very disappointing.", "Good value for money.",
        "Would recommend to friends.", "Do not buy this garbage.",
        "Solid product, fast delivery.", "Average, nothing special.",
    ]
    df_raw = pd.DataFrame([{
        'user_id': f'U{random.randint(1,50)}',
        'asin': f'ASIN{random.randint(1,20)}',
        'title': random.choice(sample_texts)[:40],
        'text': random.choice(sample_texts),
        'rating': random.randint(1, 5),
        'verified_purchase': random.choice([True, False]),
        'helpful_vote': random.randint(0, 20),
        'timestamp': int((datetime.now() - timedelta(days=random.randint(0,500))).timestamp() * 1000),
        'parent_asin': f'ASIN{random.randint(1,20)}',
    } for _ in range(500)])


# ── Step 2: Normalize columns ─────────────────────────────────────────────────
print("[2/6] Normalizing columns...")

def get_col(df, *candidates):
    for c in candidates:
        if c in df.columns:
            return df[c]
    return pd.Series([''] * len(df))

df = pd.DataFrame()
df['user_id']           = get_col(df_raw, 'user_id', 'reviewerID', 'reviewer_id')
df['product']           = get_col(df_raw, 'parent_asin', 'asin', 'product_id')
df['review_text']       = get_col(df_raw, 'text', 'reviewText', 'body', 'comment')
df['review_title']      = get_col(df_raw, 'title', 'summary', 'review_title')
df['rating']            = pd.to_numeric(get_col(df_raw, 'rating', 'overall', 'stars'), errors='coerce').fillna(3).clip(1, 5).astype(int)
df['verified_purchase'] = get_col(df_raw, 'verified_purchase', 'verified', 'verifiedPurchase').astype(bool)
df['helpful_vote']      = pd.to_numeric(get_col(df_raw, 'helpful_vote', 'helpful', 'helpfulVotes'), errors='coerce').fillna(0).astype(int)

# Parse timestamp → datetime
raw_ts = get_col(df_raw, 'timestamp', 'unixReviewTime', 'review_time', 'date')
def parse_ts(v):
    try:
        v = float(v)
        # milliseconds vs seconds
        if v > 1e11:
            v = v / 1000
        return datetime.fromtimestamp(v, tz=timezone.utc)
    except:
        return datetime.now(tz=timezone.utc) - timedelta(days=np.random.randint(0, 365))

df['review_dt'] = raw_ts.apply(parse_ts)

# Combine title + text for richer text analysis
df['full_text'] = (df['review_title'].fillna('') + ' ' + df['review_text'].fillna('')).str.strip()

# Drop rows with no text or no user_id
df = df[df['full_text'].str.len() > 5]
df = df[df['user_id'].str.len() > 0]
df = df.reset_index(drop=True)
print(f"  Clean rows: {len(df)}\n")


# ── Step 3: Per-user behavioral features ─────────────────────────────────────
print("[3/6] Computing per-user behavioral features...")

# Group all reviews per user
user_groups = df.groupby('user_id')

user_features = {}
for uid, grp in user_groups:
    grp = grp.sort_values('review_dt')
    dates   = list(grp['review_dt'])
    ratings = list(grp['rating'])
    texts   = list(grp['full_text'].fillna(''))
    n       = len(dates)

    # account_age: days between first and last review (proxy for account activity span)
    if n >= 2:
        age_days = max((dates[-1] - dates[0]).days, 1)
    else:
        age_days = 30  # assume 30-day-old account for single-review users

    # reviews_per_day
    reviews_per_day = round(n / age_days, 5)

    # verified_purchase_ratio
    verified_ratio = round(grp['verified_purchase'].mean(), 4)

    # rating_deviation: how extreme this user's ratings are vs global mean (3.5)
    avg_rating = np.mean(ratings)
    rating_deviation = round(abs(avg_rating - 3.5), 4)

    # burstiness: max reviews in any 7-day window normalised by weekly average
    max_in_window = 1
    for i, d in enumerate(dates):
        window_end = d + timedelta(days=7)
        count = sum(1 for dd in dates if d <= dd <= window_end)
        max_in_window = max(max_in_window, count)
    weekly_avg = max(n / (age_days / 7), 1)
    burstiness = round(max_in_window / weekly_avg, 4)

    # helpfulness_ratio
    helpful_count = int(grp['helpful_vote'].gt(0).sum())
    helpfulness_ratio = round(helpful_count / n, 4)

    # night_review_ratio: reviews between 1am–5am UTC
    night_count = sum(1 for d in dates if 1 <= d.hour <= 5)
    night_review_ratio = round(night_count / n, 4)

    user_features[uid] = {
        'account_age':            float(age_days),
        'reviews_per_day':        reviews_per_day,
        'verified_purchase_ratio': verified_ratio,
        'rating_deviation':        rating_deviation,
        'burstiness':             burstiness,
        'helpfulness_ratio':      helpfulness_ratio,
        'night_review_ratio':     night_review_ratio,
        '_texts':                 texts,
        '_ratings':               ratings,
        '_products':              list(grp['product']),
    }

print(f"  Computed features for {len(user_features)} unique users\n")


# ── Step 4: Similarity score (TF-IDF cosine per user) ────────────────────────
print("[4/6] Computing review similarity scores (copy-paste detection)...")

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as cos_sim

for uid, feat in user_features.items():
    texts = feat['_texts']
    if len(texts) >= 2:
        try:
            vec = TfidfVectorizer(max_features=200, min_df=1).fit_transform(texts)
            sim_matrix = cos_sim(vec)
            # Average off-diagonal similarity
            n = sim_matrix.shape[0]
            if n > 1:
                off_diag = sim_matrix[np.triu_indices(n, k=1)]
                feat['similarity_score'] = round(float(np.mean(off_diag)), 4)
            else:
                feat['similarity_score'] = 0.0
        except:
            feat['similarity_score'] = 0.0
    else:
        feat['similarity_score'] = 0.0

print("  Done\n")


# ── Step 5: Sentiment-rating mismatch (VADER) ─────────────────────────────────
print("[5/6] Computing sentiment-rating mismatch (VADER)...")

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
vader = SentimentIntensityAnalyzer()

# Compute per-review mismatch, then aggregate per user
df['vader_compound'] = df['full_text'].apply(lambda t: vader.polarity_scores(str(t))['compound'])

# Expected rating from sentiment: map [-1,1] → [1,5]
df['expected_rating'] = ((df['vader_compound'] + 1) / 2 * 4 + 1).clip(1, 5)
df['mismatch']        = (abs(df['rating'] - df['expected_rating']) / 4).clip(0, 1)

user_mismatch = df.groupby('user_id')['mismatch'].mean().round(4)
for uid, feat in user_features.items():
    feat['sentiment_rating_mismatch'] = float(user_mismatch.get(uid, 0.0))

print("  Done\n")


# ── Step 6: Reviewer overlap score ───────────────────────────────────────────
print("[6/6] Computing reviewer overlap scores...")

# Build product → set of reviewers index
product_reviewers = defaultdict(set)
for uid, feat in user_features.items():
    for pid in feat['_products']:
        product_reviewers[pid].add(uid)

for uid, feat in user_features.items():
    user_products = set(feat['_products'])
    co_reviewer_counts = defaultdict(int)
    for pid in user_products:
        for other_uid in product_reviewers[pid]:
            if other_uid != uid:
                co_reviewer_counts[other_uid] += 1
    # Count co-reviewers who share 2+ products with this user
    overlap_users = sum(1 for cnt in co_reviewer_counts.values() if cnt >= 2)
    total_co_reviewers = len(co_reviewer_counts)
    feat['reviewer_overlap_score'] = round(
        min(overlap_users / max(total_co_reviewers, 1), 1.0), 4
    )

print("  Done\n")


# ── Assemble final CSV ────────────────────────────────────────────────────────
print("Assembling final dataset...")

output_rows = []
for _, row in df.iterrows():
    uid  = row['user_id']
    feat = user_features.get(uid, {})
    if not feat:
        continue

    output_rows.append({
        'product':                   row['product'],
        'review_text':               str(row['full_text'])[:500],   # cap at 500 chars
        'rating':                    int(row['rating']),
        'account_age':               feat.get('account_age', 30),
        'reviews_per_day':           feat.get('reviews_per_day', 0.1),
        'verified_purchase_ratio':   feat.get('verified_purchase_ratio', 0.5),
        'rating_deviation':          feat.get('rating_deviation', 0.5),
        'burstiness':                feat.get('burstiness', 0.5),
        'helpfulness_ratio':         feat.get('helpfulness_ratio', 0.3),
        'similarity_score':          feat.get('similarity_score', 0.0),
        'sentiment_rating_mismatch': feat.get('sentiment_rating_mismatch', 0.0),
        'night_review_ratio':        feat.get('night_review_ratio', 0.0),
        'reviewer_overlap_score':    feat.get('reviewer_overlap_score', 0.0),
    })

out_df = pd.DataFrame(output_rows)

# Remove duplicates and shuffle
out_df = out_df.drop_duplicates(subset=['review_text']).sample(frac=1, random_state=42).reset_index(drop=True)

out_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"  ✅  Dataset saved: {OUTPUT_FILE}")
print(f"  Total reviews   : {len(out_df)}")
print(f"  Unique products : {out_df['product'].nunique()}")
print(f"  Rating dist     : {dict(out_df['rating'].value_counts().sort_index())}")
print(f"\n  Metadata ranges:")
for col in ['account_age','reviews_per_day','burstiness','similarity_score',
            'sentiment_rating_mismatch','night_review_ratio','reviewer_overlap_score']:
    print(f"    {col:<32} min={out_df[col].min():.3f}  max={out_df[col].max():.3f}  mean={out_df[col].mean():.3f}")
print(f"\n  Upload this CSV to:")
print(f"  ReviewGuard → Admin Dashboard → Upload CSV")
print(f"  The model will classify each review automatically.")
print(f"{'='*60}\n")
