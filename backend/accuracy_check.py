import asyncio
import json
from app.db import AsyncSessionLocal
from app.models import Review
from sqlalchemy import select, func

async def check_accuracy():
    async with AsyncSessionLocal() as db:
        print("=" * 70)
        print("🤖 ML MODEL ACCURACY ANALYSIS")
        print("=" * 70)
        
        # Get all reviews with verdicts
        result = await db.execute(select(Review).where(Review.verdict != None))
        all_reviews = result.scalars().all()
        print(f"\nTotal reviews with verdicts: {len(all_reviews)}")
        
        # Count by verdict
        fake_count = len([r for r in all_reviews if r.verdict == 'fake'])
        genuine_count = len([r for r in all_reviews if r.verdict == 'genuine'])
        
        print(f"\nVerdict Distribution:")
        print(f"  • Fake reviews:    {fake_count} ({fake_count/len(all_reviews)*100:.1f}%)")
        print(f"  • Genuine reviews: {genuine_count} ({genuine_count/len(all_reviews)*100:.1f}%)")
        
        # Confidence analysis
        print(f"\n📊 Confidence Score Statistics:")
        confidences = [r.confidence for r in all_reviews if r.confidence is not None]
        if confidences:
            avg_conf = sum(confidences) / len(confidences)
            min_conf = min(confidences)
            max_conf = max(confidences)
            print(f"  • Average confidence: {avg_conf*100:.1f}%")
            print(f"  • Min confidence:     {min_conf*100:.1f}%")
            print(f"  • Max confidence:     {max_conf*100:.1f}%")
        
        # Genuine probability analysis
        print(f"\n📊 Genuine Probability Statistics:")
        gen_probs = [r.genuine_probability for r in all_reviews if r.genuine_probability is not None]
        if gen_probs:
            avg_gen = sum(gen_probs) / len(gen_probs)
            print(f"  • Average: {avg_gen*100:.1f}%")
        
        # Check for high confidence predictions
        high_conf = [r for r in all_reviews if r.confidence and r.confidence >= 0.9]
        low_conf = [r for r in all_reviews if r.confidence and r.confidence <= 0.6]
        
        print(f"\n🎯 Confidence Levels:")
        print(f"  • High confidence (≥90%): {len(high_conf)} reviews ({len(high_conf)/len(all_reviews)*100:.1f}%)")
        print(f"  • Low confidence (≤60%):  {len(low_conf)} reviews ({len(low_conf)/len(all_reviews)*100:.1f}%)")
        
        # Fusion strategy
        strategies = {}
        for r in all_reviews:
            if r.fusion_strategy:
                strategies[r.fusion_strategy] = strategies.get(r.fusion_strategy, 0) + 1
        
        if strategies:
            print(f"\n🔗 Fusion Strategies Used:")
            for strategy, count in sorted(strategies.items(), key=lambda x: x[1], reverse=True):
                print(f"  • {strategy}: {count} reviews")
        
        # Sample reasoning analysis
        print(f"\n💡 Sample Reasoning Data (First Review):")
        if all_reviews:
            sample = all_reviews[0]
            if sample.reasoning:
                try:
                    reasoning = json.loads(sample.reasoning)
                    print(f"  Review ID: {sample.id}")
                    print(f"  Verdict: {sample.verdict}")
                    print(f"  Confidence: {sample.confidence*100:.1f}%")
                    print(f"  Fusion Strategy: {reasoning.get('fusion_strategy', 'N/A')}")
                    
                    modal_scores = reasoning.get('modal_scores', {})
                    print(f"  Modal Scores:")
                    print(f"    • Text score: {modal_scores.get('text_score', 'N/A')}")
                    print(f"    • Metadata score: {modal_scores.get('metadata_score', 'N/A')}")
                    
                    attn = reasoning.get('attention_weights', {})
                    print(f"  Attention Weights:")
                    print(f"    • Text: {attn.get('text', 'N/A')}")
                    print(f"    • Metadata: {attn.get('metadata', 'N/A')}")
                except:
                    pass
        
        print("\n" + "=" * 70)

asyncio.run(check_accuracy())
