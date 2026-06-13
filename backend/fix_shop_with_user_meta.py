#!/usr/bin/env python3
import re

# Read the file
with open('/app/app/api/shop.py', 'r') as f:
    lines = f.readlines()

# Find the bounded_inference function and replace it
output = []
i = 0
skip_until_return = False

while i < len(lines):
    line = lines[i]
    
    # Check if this is the start of bounded_inference
    if 'async def bounded_inference(text, rating, meta, label_verdict):' in line:
        # Replace the entire function
        output.append(line)  # Keep the def line
        i += 1
        
        # Skip old content until we find the return statement
        indent_count = 0
        while i < len(lines):
            if 'return (text, rating, verdict' in lines[i]:
                i += 1
                break
            i += 1
        
        # Insert new content
        new_func = '''                async with semaphore:
                    ml = await run_inference(client, text, rating, meta)
                    ai_verdict = ml.get("verdict")
                    confidence = ml.get("confidence")
                    genuine_prob = ml.get("genuine_probability")
                    verdict = label_verdict if label_verdict else ai_verdict
                    
                    # Fetch real user metadata from database
                    user_meta = {}
                    if user and user.id:
                        try:
                            user_meta_result = await db.execute(
                                select(Review).where(Review.user_id == user.id)
                            )
                            user_reviews = user_meta_result.scalars().all()
                            from datetime import timedelta
                            import math
                            
                            account_age = max((datetime.utcnow() - user.created_at).days, 1)
                            total_reviews = len(user_reviews)
                            reviews_per_day = round(total_reviews / account_age, 4)
                            
                            orders_result = await db.execute(
                                select(Order).where(Order.user_id == user.id)
                            )
                            orders = orders_result.scalars().all()
                            verified_purchase_ratio = round(len(orders) / max(total_reviews, 1), 4)
                            
                            avg_rating = sum(r.rating or 3 for r in user_reviews) / max(total_reviews, 1)
                            rating_deviation = round(abs(avg_rating - 3.5), 4)
                            
                            burstiness = 0.0
                            if total_reviews > 1:
                                dates = sorted([r.created_at for r in user_reviews if r.created_at])
                                max_in_window = 1
                                for d in dates:
                                    window_end = d + timedelta(days=7)
                                    count = sum(1 for dd in dates if d <= dd <= window_end)
                                    max_in_window = max(max_in_window, count)
                                burstiness = round(max_in_window / max(account_age / 7, 1), 4)
                            
                            helpful_count = sum(1 for r in user_reviews if getattr(r, 'helpful_votes', 0) and r.helpful_votes > 0)
                            helpfulness_ratio = round(helpful_count / max(total_reviews, 1), 4)
                            
                            similarity_score = 0.0
                            texts = [r.text or '' for r in user_reviews if r.text]
                            if len(texts) >= 2:
                                def word_set(t): return set(t.lower().split())
                                overlaps = []
                                for i_idx in range(min(len(texts), 10)):
                                    for j_idx in range(i_idx + 1, min(len(texts), 10)):
                                        a, b = word_set(texts[i_idx]), word_set(texts[j_idx])
                                        if a and b:
                                            overlaps.append(len(a & b) / math.sqrt(len(a) * len(b)))
                                similarity_score = round(sum(overlaps) / max(len(overlaps), 1), 4) if overlaps else 0.0
                            
                            mismatch_count = 0
                            negative_words = {'bad', 'terrible', 'awful', 'horrible', 'worst', 'poor', 'waste', 'broken', 'damaged', 'useless', 'disappointed', 'disappointing', 'defective'}
                            positive_words = {'great', 'excellent', 'amazing', 'perfect', 'love', 'best', 'awesome', 'fantastic', 'wonderful', 'superb', 'outstanding'}
                            for rev in user_reviews:
                                t = (rev.text or '').lower()
                                stars = rev.rating or 3
                                words = set(t.split())
                                neg_hit = bool(words & negative_words)
                                pos_hit = bool(words & positive_words)
                                if (neg_hit and stars >= 4) or (pos_hit and stars <= 2):
                                    mismatch_count += 1
                            sentiment_rating_mismatch = round(mismatch_count / max(total_reviews, 1), 4)
                            
                            night_count = sum(1 for r in user_reviews if r.created_at and 1 <= r.created_at.hour <= 5)
                            night_review_ratio = round(night_count / max(total_reviews, 1), 4)
                            
                            reviewer_overlap_score = 0.0
                            product_ids = [r.product_id for r in user_reviews if r.product_id]
                            if product_ids:
                                co_reviews_result = await db.execute(
                                    select(Review.user_id, func.count(Review.id).label('cnt'))
                                    .where(Review.product_id.in_(product_ids))
                                    .where(Review.user_id != user.id)
                                    .group_by(Review.user_id)
                                )
                                co_reviewers = co_reviews_result.all()
                                overlap_users = sum(1 for _, cnt in co_reviewers if cnt >= 3)
                                reviewer_overlap_score = round(min(overlap_users / max(len(product_ids), 1), 1.0), 4)
                            
                            user_meta = {
                                "account_age": account_age,
                                "reviews_per_day": reviews_per_day,
                                "verified_purchase_ratio": verified_purchase_ratio,
                                "rating_deviation": rating_deviation,
                                "burstiness": burstiness,
                                "helpfulness_ratio": helpfulness_ratio,
                                "similarity_score": similarity_score,
                                "sentiment_rating_mismatch": sentiment_rating_mismatch,
                                "night_review_ratio": night_review_ratio,
                                "reviewer_overlap_score": reviewer_overlap_score,
                            }
                        except:
                            pass
                    
                    # Merge user metadata with CSV metadata (CSV takes precedence)
                    if ml:
                        ml["metadata_features"] = {}
                        # First add user metadata
                        for k, v in user_meta.items():
                            ml["metadata_features"][k] = v
                        # Then override with CSV metadata if present
                        for k, v in meta.items():
                            if v is not None:
                                ml["metadata_features"][k] = v
                        # If still missing any fields, use 0.5 default
                        default_keys = ["account_age", "reviews_per_day", "verified_purchase_ratio", "rating_deviation", "burstiness", "helpfulness_ratio", "similarity_score", "sentiment_rating_mismatch", "night_review_ratio", "reviewer_overlap_score"]
                        for k in default_keys:
                            if k not in ml["metadata_features"]:
                                ml["metadata_features"][k] = 0.5
                    
                    reasoning = _build_reasoning(ml) if ml else None
                    return (text, rating, verdict, confidence, genuine_prob, ml.get("fusion_strategy"), reasoning)
'''
        output.append(new_func)
    else:
        output.append(line)
    i += 1

# Write back
with open('/app/app/api/shop.py', 'w') as f:
    f.writelines(output)

print("Updated shop.py with real user metadata extraction")
