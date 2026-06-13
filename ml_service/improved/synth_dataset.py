"""Realistic synthetic dataset generator for fake review detection.

Generates jointly-aligned (text, metadata, label) rows that follow plausible
real-world patterns observed in literature:

Genuine reviewers (label=0):
  - longer-tail account age, low reviews_per_day, high verified_purchase_ratio,
  - moderate rating_deviation, low burstiness, mixed sentiment,
  - varied text (specific nouns, mixed superlatives, mentions of usage),
  - text sentiment broadly consistent with star rating.

Fake/spam reviewers (label=1):
  - young accounts, many reviews/day, low verified ratio, high rating deviation,
  - bursty posting, high copy-paste similarity, night-time posting,
  - text is either an over-the-top 5-star puff piece or a 1-star hit piece,
  - heavy superlatives, low specificity, low pronoun ratio, sentiment-rating
    mismatch is more common.

The text generator is template-based but deliberately diverse so models
actually have to learn lexical patterns (not memorise a single string).
"""
from __future__ import annotations

import argparse
import os
import random
from pathlib import Path

import numpy as np
import pandas as pd

RNG = np.random.default_rng(7)

# ---------------------------------------------------------------------------
# Vocabulary pools
# ---------------------------------------------------------------------------

GENUINE_OPENERS = [
    "Bought this", "Got this", "Have been using this", "Picked this up",
    "Ordered this last", "Tried this for", "Been testing this", "Switched to this from",
    "I purchased this", "We've had this", "After a few weeks with this", "Bought as a gift",
]

GENUINE_DETAILS = [
    "the battery lasts about two days on a single charge",
    "the stitching looks clean and even on both sides",
    "it heats up faster than my old one but the handle still stays cool",
    "the app paired on the second try but works fine after that",
    "size runs slightly small, I'd recommend going one up",
    "color is closer to navy than the photos suggest",
    "the filter is easy to rinse out and dries quickly",
    "noise level is noticeable on the highest setting but acceptable",
    "instructions were sparse so I watched a quick video to set it up",
    "it fits in my standard cabinet with about an inch to spare",
    "after a month it still works as expected, no flaking or fading",
    "the seal isn't perfect but it hasn't leaked in my bag",
    "shipping took a week and the box arrived slightly dented",
    "I compared it side by side with my older model from another brand",
]

GENUINE_CLOSERS = [
    "Overall, happy with the purchase for the price.",
    "Would buy again, with the caveats above.",
    "Solid for everyday use, not a luxury item.",
    "Recommend if you understand the trade-offs.",
    "Four stars because of the minor issues I mentioned.",
    "Decent value, nothing extraordinary.",
    "Will update this review after another month of use.",
]

FAKE_5STAR_PHRASES = [
    "AMAZING product!!! Best ever!!!",
    "Absolutely perfect, 10/10, must buy now!!!",
    "Best purchase of my life, you will not regret it!",
    "Incredible quality, fantastic seller, FIVE STARS!",
    "Love love love it!! Highly recommend to everyone!!",
    "This product changed my life, buy it immediately!",
    "Wow! Amazing! Perfect in every way! Best best best!",
    "Excellent excellent excellent, the best on the market.",
    "Outstanding outstanding, a true masterpiece, awesome!",
    "Perfect perfect perfect, nothing else compares.",
]

FAKE_1STAR_PHRASES = [
    "Terrible terrible terrible, do not buy this scam.",
    "Worst product ever, complete waste of money, AVOID!",
    "Absolute garbage, total scam, the seller is a fraud.",
    "Horrible horrible horrible, ZERO stars if I could.",
    "Awful, useless, broken, never again, AVOID this seller!",
    "Total scam, fake reviews everywhere, don't fall for it.",
    "Worst worst worst, I want my money back immediately.",
    "Useless useless useless, total ripoff.",
]

FAKE_TEMPLATES = [
    "{phrase} You must buy this {product}!",
    "{phrase} Everyone needs this {product} in their life.",
    "{phrase} Best {product} ever made.",
    "{phrase} {phrase}",
    "{phrase}",
]

PRODUCTS = [
    "phone case", "blender", "headphones", "kettle", "yoga mat",
    "office chair", "watch", "knife set", "lamp", "backpack",
    "monitor", "vacuum", "cookware", "skincare cream", "running shoes",
]


def _genuine_text(rating: int) -> str:
    """Generate a plausible genuine review consistent with the rating."""
    opener = random.choice(GENUINE_OPENERS)
    n_details = random.choices([1, 2, 3, 4], weights=[2, 4, 3, 1])[0]
    details = random.sample(GENUINE_DETAILS, k=min(n_details, len(GENUINE_DETAILS)))
    closer = random.choice(GENUINE_CLOSERS)

    # Sentiment tone aligned with rating
    if rating <= 2:
        sentiment = random.choice([
            "but the main issue is that it stopped working after a few days",
            "however the quality is below what I expected for the price",
            "unfortunately the part I needed most arrived broken",
        ])
        closer = random.choice([
            "Returning this, sadly.",
            "Two stars because the brand handled the return well.",
            "Can't recommend at this price.",
        ])
    elif rating == 3:
        sentiment = random.choice([
            "it does the basics but nothing more",
            "fine for the price, nothing exciting",
            "works as advertised, no surprises good or bad",
        ])
    else:
        sentiment = random.choice([
            "and so far I'm pleased with how it performs day to day",
            "and it's held up better than I expected",
            "and I'd buy it again at this price",
        ])

    body = f"{opener} {random.choice(['last month', 'in March', 'for my partner', 'for the kitchen', 'for travel'])}, {sentiment}. " \
           + " ".join(d.capitalize() + "." for d in details) + " " + closer
    return body


def _fake_text(rating: int) -> str:
    """Generate a fake review – polarised, generic, heavy superlatives."""
    if rating >= 4:
        phrase = random.choice(FAKE_5STAR_PHRASES)
    elif rating <= 2:
        phrase = random.choice(FAKE_1STAR_PHRASES)
    else:
        # rare mid-rating fakes – usually sentiment mismatched (5-star wording, 3 stars)
        phrase = random.choice(FAKE_5STAR_PHRASES + FAKE_1STAR_PHRASES)
    template = random.choice(FAKE_TEMPLATES)
    text = template.format(phrase=phrase, product=random.choice(PRODUCTS))

    # Inject ALL CAPS bursts and repeated punctuation that real spammers love
    if random.random() < 0.4:
        text = text.upper()
    if random.random() < 0.3:
        text = text.replace("!", "!!!")
    if random.random() < 0.25:
        text += " " + " ".join(random.sample(
            ["GREAT", "PERFECT", "AMAZING", "BUY NOW", "MUST HAVE"], k=3
        ))
    return text


def _genuine_metadata():
    """Plausible metadata for a genuine reviewer."""
    account_age = float(np.clip(RNG.normal(420, 180), 30, 1500))      # ~14 months avg
    reviews_per_day = float(np.clip(RNG.exponential(0.15), 0, 3))     # mostly < 0.5
    verified = float(np.clip(RNG.beta(8, 2), 0, 1))                   # mostly >0.7
    rating_deviation = float(np.clip(abs(RNG.normal(0.4, 0.4)), 0, 4))
    burstiness = float(np.clip(RNG.exponential(0.6), 0, 5))
    helpfulness = float(np.clip(RNG.beta(5, 3), 0, 1))                # skewed high
    similarity = float(np.clip(RNG.beta(2, 8), 0, 1))                 # low copy-paste
    sent_mismatch = float(np.clip(abs(RNG.normal(0.05, 0.08)), 0, 1)) # low
    night_ratio = float(np.clip(RNG.beta(2, 10), 0, 1))               # low
    overlap = float(np.clip(RNG.beta(2, 10), 0, 1))                   # low
    return dict(
        account_age=account_age, reviews_per_day=reviews_per_day,
        verified_purchase_ratio=verified, rating_deviation=rating_deviation,
        burstiness=burstiness, helpfulness_ratio=helpfulness,
        similarity_score=similarity, sentiment_rating_mismatch=sent_mismatch,
        night_review_ratio=night_ratio, reviewer_overlap_score=overlap,
    )


def _fake_metadata():
    """Plausible metadata for a fake/spam reviewer."""
    account_age = float(np.clip(RNG.exponential(60), 0, 800))         # young
    reviews_per_day = float(np.clip(RNG.gamma(2.5, 1.0), 0, 15))      # high
    verified = float(np.clip(RNG.beta(2, 6), 0, 1))                   # low
    rating_deviation = float(np.clip(abs(RNG.normal(1.6, 0.9)), 0, 4))
    burstiness = float(np.clip(RNG.gamma(3.0, 0.9), 0, 8))            # high
    helpfulness = float(np.clip(RNG.beta(2, 7), 0, 1))                # low
    similarity = float(np.clip(RNG.beta(7, 2), 0, 1))                 # high copy-paste
    sent_mismatch = float(np.clip(abs(RNG.normal(0.45, 0.25)), 0, 1)) # high
    night_ratio = float(np.clip(RNG.beta(6, 4), 0, 1))                # higher
    overlap = float(np.clip(RNG.beta(6, 3), 0, 1))                    # higher
    return dict(
        account_age=account_age, reviews_per_day=reviews_per_day,
        verified_purchase_ratio=verified, rating_deviation=rating_deviation,
        burstiness=burstiness, helpfulness_ratio=helpfulness,
        similarity_score=similarity, sentiment_rating_mismatch=sent_mismatch,
        night_review_ratio=night_ratio, reviewer_overlap_score=overlap,
    )


def generate(n: int = 6000, fake_ratio: float = 0.5, seed: int = 7,
             noise_rate: float = 0.18) -> pd.DataFrame:
    """Return a DataFrame with text + metadata columns + label.

    ``noise_rate`` controls how often we generate realistic *confusers* so the
    classification problem is not trivially separable:
      - Genuine reviewers that occasionally post a short enthusiastic review
        ("Love it!!!") with otherwise normal metadata.
      - Sophisticated fakes that mimic the genuine writing style (specific
        details, mixed sentiment) while still being from a young account.
      - Metadata-only confusers: a few genuine accounts that look bursty after
        a vacation purchase, a few fake accounts that aged a real profile.
    """
    global RNG
    RNG = np.random.default_rng(seed)
    random.seed(seed)

    n_fake = int(n * fake_ratio)
    n_genuine = n - n_fake

    rows = []

    # ---- Genuine ---------------------------------------------------------
    for _ in range(n_genuine):
        rating = int(np.clip(round(RNG.normal(4.1, 0.9)), 1, 5))
        meta = _genuine_metadata()
        if random.random() < noise_rate:
            # Short, enthusiastic but real review (looks fake-ish lexically)
            text = random.choice([
                "Love it! Works great.",
                "Perfect, exactly what I needed!",
                "Amazing, would buy again!",
                "Best purchase this year, no complaints.",
                "Excellent quality for the price!",
            ])
            if random.random() < 0.5:
                text = text.upper()
        else:
            text = _genuine_text(rating)
            # Occasionally a genuine reviewer has a bursty week (vacation buys, etc.)
            if random.random() < noise_rate / 2:
                meta["reviews_per_day"] = float(np.clip(RNG.gamma(2.0, 1.0), 0, 6))
                meta["burstiness"] = float(np.clip(RNG.gamma(2.5, 0.9), 0, 6))
        rows.append({"text": text, "rating": rating, "label": 0, **meta})

    # ---- Fake ------------------------------------------------------------
    for _ in range(n_fake):
        rating = int(random.choices([1, 2, 4, 5], weights=[3, 1, 1, 6])[0])
        meta = _fake_metadata()
        if random.random() < noise_rate:
            # Sophisticated fake: imitate a genuine-looking long review
            text = _genuine_text(rating)
            # but still posted from a young / bursty account
        else:
            text = _fake_text(rating)
            # Occasionally a fake reviewer has aged a profile (low burst, high age)
            if random.random() < noise_rate / 2:
                meta["account_age"] = float(np.clip(RNG.normal(500, 200), 30, 1500))
                meta["verified_purchase_ratio"] = float(np.clip(RNG.beta(5, 3), 0, 1))
                meta["reviews_per_day"] = float(np.clip(RNG.exponential(0.2), 0, 2))
        rows.append({"text": text, "rating": rating, "label": 1, **meta})

    # ---- Label flip noise (real-world labelling is imperfect) -----------
    df = pd.DataFrame(rows).sample(frac=1.0, random_state=seed).reset_index(drop=True)
    flip_idx = df.sample(frac=0.03, random_state=seed).index  # 3% label noise
    df.loc[flip_idx, "label"] = 1 - df.loc[flip_idx, "label"]
    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(Path(__file__).parent / "data"))
    parser.add_argument("--n", type=int, default=6000)
    parser.add_argument("--fake-ratio", type=float, default=0.5)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = generate(n=args.n, fake_ratio=args.fake_ratio, seed=args.seed)

    full_path = out_dir / "synth_full.csv"
    text_path = out_dir / "synth_text.csv"
    meta_path = out_dir / "synth_metadata.csv"

    df.to_csv(full_path, index=False)
    df[["text", "rating", "label"]].to_csv(text_path, index=False)
    meta_cols = [
        "account_age", "reviews_per_day", "verified_purchase_ratio",
        "rating_deviation", "burstiness", "helpfulness_ratio",
        "similarity_score", "sentiment_rating_mismatch",
        "night_review_ratio", "reviewer_overlap_score", "label",
    ]
    df[meta_cols].to_csv(meta_path, index=False)

    print(f"Wrote {len(df)} rows to {full_path}")
    print(f"  Text:     {text_path}")
    print(f"  Metadata: {meta_path}")
    print("Label distribution:")
    print(df["label"].value_counts().to_string())


if __name__ == "__main__":
    main()
