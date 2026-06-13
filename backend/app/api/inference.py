import json
from datetime import datetime
from typing import Any, Optional

import httpx
from celery.result import AsyncResult
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, select, func, delete as sql_delete
import os

from app.celery_worker import celery_app, run_inference_task
from app.db import get_db
from app.models import Review, AuditLog
from app.schemas import ReviewOut, AuditLogOut, AuditLogPage
from app.api.auth import get_optional_user, get_current_user

ML_SERVICE_URL = os.getenv('ML_SERVICE_URL', 'http://ml_inference:8501').rstrip('/')
if ML_SERVICE_URL.endswith('/predict'):
    ML_SERVICE_URL = ML_SERVICE_URL[:-len('/predict')]

router = APIRouter()


# ── Reasoning helper (mirrors shop.py) ───────────────────────

def _build_reasoning(ml: dict) -> str | None:
    if not ml:
        return None
    try:
        modal_scores   = ml.get("modal_scores") or {}
        attention      = ml.get("attention") or {}
        text_features  = ml.get("text_features") or {}
        modal_details  = ml.get("modal_details") or {}
        meta_explain   = modal_details.get("meta") or {}
        # Raw metadata — the ML service echoes back the full metadata_features dict
        raw_meta = ml.get("metadata_features") or {}
        # Fallback: if metadata_features missing, pull from modal_details.meta
        if not raw_meta and isinstance(meta_explain, dict):
            raw_meta = meta_explain

        # Linguistic signals from text_features dict
        linguistic = {}
        if isinstance(text_features, dict):
            linguistic = {
                "superlative_count":  text_features.get("superlative_count", 0),
                "readability":        text_features.get("readability", 0),
                "sentence_variance":  text_features.get("sentence_variance", 0),
                "pronoun_ratio":      text_features.get("pronoun_ratio", 0),
                "sentiment_mismatch": text_features.get("sentiment_mismatch", 0),
            }

        # Top metadata signals — store all raw values directly
        META_LABELS = [
            ("similarity_score",          "Similarity Score"),
            ("reviewer_overlap_score",    "Reviewer Overlap"),
            ("sentiment_rating_mismatch", "Sentiment Mismatch"),
            ("rating_deviation",          "Rating Deviation"),
            ("burstiness",                "Burstiness"),
            ("helpfulness_ratio",         "Helpfulness Ratio"),
            ("night_review_ratio",        "Night Review Ratio"),
            ("verified_purchase_ratio",   "Verified Purchase"),
            ("reviews_per_day",           "Reviews Per Day"),
            ("account_age",               "Account Age (days)"),
        ]
        top_meta_signals = []
        for key, label in META_LABELS:
            val = raw_meta.get(key)
            if val is not None:
                top_meta_signals.append({"feature": label, "value": round(float(val), 4)})

        # Normalise modal_scores: text/meta → text_score/metadata_score
        ms = {}
        if modal_scores.get("text") is not None:
            ms["text_score"]     = round(float(modal_scores["text"]), 4)
        if modal_scores.get("meta") is not None:
            ms["metadata_score"] = round(float(modal_scores["meta"]), 4)

        confidence   = ml.get("confidence")
        genuine_prob = ml.get("genuine_probability")

        return json.dumps({
            "verdict":             ml.get("verdict"),
            "confidence":          round(confidence, 4) if confidence is not None else None,
            "genuine_probability": round(genuine_prob, 4) if genuine_prob is not None else None,
            "fusion_strategy":     ml.get("fusion_strategy"),
            "modal_scores":        ms,
            "attention_weights":   {k: round(float(v), 4) if v is not None else None for k, v in attention.items()},
            "linguistic":          linguistic,
            "top_meta_signals":    top_meta_signals,
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return None

class InferenceResponse(BaseModel):
    verdict: str
    confidence: float
    genuine_probability: float
    attention: dict[str, float]
    fusion_strategy: str
    modal_scores: dict[str, Optional[float]]
    modal_details: dict[str, Any]
    text_features: Optional[dict[str, Any]] = None
    metadata_features: Optional[dict[str, Any]] = None
    roc_curves: Optional[dict[str, float]] = None


class TaskResponse(BaseModel):
    task_id: str
    status: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[dict[str, Any]] = None


async def _proxy_ml_service(path: str, data: dict | None = None, method: str = 'POST'):
    async with httpx.AsyncClient(timeout=60.0) as client:
        if method == 'GET':
            response = await client.get(f"{ML_SERVICE_URL}{path}")
        else:
            response = await client.post(f"{ML_SERVICE_URL}{path}", data=data or {})
        response.raise_for_status()
        return response.json()


# ── Reviews ──────────────────────────────────────────────────

@router.get('/reviews', response_model=list[ReviewOut])
async def list_reviews(
    limit: int = 25, skip: int = 0,
    verdict: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_optional_user),
):
    base = select(Review).order_by(desc(Review.created_at))
    if verdict == 'pending':
        base = base.where(Review.verdict == None)
    elif verdict in ('fake', 'genuine'):
        base = base.where(Review.verdict == verdict)
    if user is not None and getattr(user, 'is_admin', False):
        query = base.offset(skip).limit(min(limit, 100))
    elif user is not None:
        query = base.where(Review.user_id == user.id).offset(skip).limit(min(limit, 100))
    else:
        query = base.offset(skip).limit(min(limit, 100))
    result = await db.execute(query)
    return result.scalars().all()


@router.get('/reviews/flagged', response_model=list[ReviewOut])
async def list_flagged_reviews(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    if not getattr(user, 'is_admin', False):
        raise HTTPException(status_code=403, detail='Admin privileges required')
    query = select(Review).where(Review.flagged == True).order_by(desc(Review.created_at)).limit(min(limit, 100))
    result = await db.execute(query)
    return result.scalars().all()


@router.get('/audit', response_model=AuditLogPage)
async def list_audit_logs(
    page: int = 1, page_size: int = 50,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    if not getattr(user, 'is_admin', False):
        raise HTTPException(status_code=403, detail='Admin privileges required')
    if page < 1:
        raise HTTPException(status_code=400, detail='page must be >= 1')
    page_size = max(1, min(page_size, 500))
    offset = (page - 1) * page_size
    total_res = await db.execute(select(func.count()).select_from(AuditLog))
    total = int(total_res.scalar_one() or 0)
    query = select(AuditLog).order_by(desc(AuditLog.created_at)).offset(offset).limit(page_size)
    result = await db.execute(query)
    logs = result.scalars().all()

    # Resolve actor usernames in one query
    from app.models import User as UserModel
    actor_ids = {log.actor_user_id for log in logs if log.actor_user_id}
    user_map: dict[int, str] = {}
    if actor_ids:
        u_res = await db.execute(select(UserModel).where(UserModel.id.in_(actor_ids)))
        for u in u_res.scalars().all():
            user_map[u.id] = u.username

    items = []
    for log in logs:
        d = {
            "id": log.id,
            "actor_user_id": log.actor_user_id,
            "actor_username": log.actor_username or user_map.get(log.actor_user_id),
            "action": log.action,
            "target_review_id": log.target_review_id,
            "target_order_id": getattr(log, 'target_order_id', None),
            "details": log.details,
            "created_at": log.created_at,
        }
        items.append(d)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post('/reviews/backfill-reasoning')
async def backfill_reasoning(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    if not (getattr(user, 'is_admin', False) or getattr(user, 'role', '') == 'Admin'):
       raise HTTPException(status_code=403, detail='Admin only')
    result = await db.execute(select(Review).where(Review.text != None))
    reviews = result.scalars().all()
    updated = 0
    errors = 0
    async with httpx.AsyncClient(timeout=60) as client:
        for r in reviews:
            try:
                form = {
                    "text": r.text or "",
                    "rating": str(r.rating or 3),
                    "fusion_strategy": "attention",
                }
                resp = await client.post(
                    f"{ML_SERVICE_URL}/predict",
                    data=form,
                )
                if resp.status_code != 200:
                    errors += 1
                    continue
                ml = resp.json()
                ml["metadata_features"] = ml.get("metadata_features") or {}
                reasoning = _build_reasoning(ml)
                # Always overwrite — force update even if reasoning already exists
                r.reasoning = reasoning
                r.verdict = ml.get("verdict", r.verdict)
                r.confidence = ml.get("confidence", r.confidence)
                r.genuine_probability = ml.get("genuine_probability", r.genuine_probability)
                r.fusion_strategy = ml.get("fusion_strategy", r.fusion_strategy)
                db.add(r)
                updated += 1
            except Exception:
                errors += 1
                continue
    await db.commit()
    return {"detail": f"Backfilled reasoning for {updated} reviews ({errors} errors)"}


@router.delete('/reviews')
async def delete_all_reviews(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    if not getattr(user, 'is_admin', False):
        raise HTTPException(status_code=403, detail='Admin privileges required')
    result = await db.execute(sql_delete(Review))
    await db.commit()
    return {'detail': f'Deleted {result.rowcount} reviews'}


@router.delete('/reviews/{review_id}')
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    if not getattr(user, 'is_admin', False):
        raise HTTPException(status_code=403, detail='Admin privileges required')
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail='Review not found')
    try:
        details = json.dumps({
            'review_id': review.id,
            'verdict': review.verdict,
            'user_id': review.user_id,
            'rating': review.rating,
            'text_snippet': (review.text[:200] + '...') if review.text and len(review.text) > 200 else review.text,
        })
    except Exception:
        details = None
    # Create audit log BEFORE deleting
    audit = AuditLog(
        actor_user_id=getattr(user, 'id', None),
        actor_username=getattr(user, 'username', None),
        action='delete_review',
        target_review_id=review.id,
        details=details,
    )
    db.add(audit)
    await db.flush()
    # Delete the review - audit log survives with target_review_id set to NULL
    await db.execute(sql_delete(Review).where(Review.id == review_id))
    await db.commit()
    return {'detail': 'deleted'}


# ── Health / Model card ───────────────────────────────────────

@router.get('/health')
async def health():
    try:
        return await _proxy_ml_service('/health', method='GET')
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get('/model-card')
async def model_card():
    try:
        return await _proxy_ml_service('/model-card', method='GET')
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


# ── Prediction ────────────────────────────────────────────────

@router.post('/predict', response_model=InferenceResponse)
async def predict(
    text: Optional[str] = Form(None),
    rating: Optional[float] = Form(None),
    account_age: Optional[float] = Form(None),
    reviews_per_day: Optional[float] = Form(None),
    verified_purchase_ratio: Optional[float] = Form(None),
    rating_deviation: Optional[float] = Form(None),
    burstiness: Optional[float] = Form(None),
    helpfulness_ratio: Optional[float] = Form(None),
    similarity_score: Optional[float] = Form(None),
    sentiment_rating_mismatch: Optional[float] = Form(None),
    night_review_ratio: Optional[float] = Form(None),
    reviewer_overlap_score: Optional[float] = Form(None),
    fusion_strategy: str = Form("attention"),
    product_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_optional_user),
):
    # Owners and admins cannot submit reviews
    if user and (getattr(user, 'is_admin', False) or getattr(user, 'role', None) == 'Owner'):
        raise HTTPException(status_code=403, detail='Owners and admins cannot submit reviews')

    payload = {
        "text": text or "",
        "rating": rating,
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
        "fusion_strategy": fusion_strategy,
    }

    task = run_inference_task.delay(payload)
    try:
        result = task.get(timeout=30)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    # Add metadata features to result for reasoning generation (required by _build_reasoning)
    if result:
        result["metadata_features"] = {
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

    review = Review(
        user_id=user.id if user else None,
        product_id=product_id,
        text=text,
        rating=int(rating) if rating is not None else None,
        verdict=result.get("verdict"),
        confidence=result.get("confidence"),
        genuine_probability=result.get("genuine_probability"),
        fusion_strategy=result.get("fusion_strategy"),
        flagged=False,
        flag_count=0,
        reasoning=_build_reasoning(result),
    )
    db.add(review)
    await db.commit()
    return result


@router.post('/predict/async', response_model=TaskResponse)
async def predict_async(
    text: Optional[str] = Form(None),
    rating: Optional[float] = Form(None),
    account_age: Optional[float] = Form(None),
    reviews_per_day: Optional[float] = Form(None),
    verified_purchase_ratio: Optional[float] = Form(None),
    rating_deviation: Optional[float] = Form(None),
    burstiness: Optional[float] = Form(None),
    helpfulness_ratio: Optional[float] = Form(None),
    fusion_strategy: str = Form("attention"),
):
    payload = {
        "text": text or "",
        "rating": rating,
        "account_age": account_age,
        "reviews_per_day": reviews_per_day,
        "verified_purchase_ratio": verified_purchase_ratio,
        "rating_deviation": rating_deviation,
        "burstiness": burstiness,
        "helpfulness_ratio": helpfulness_ratio,
        "fusion_strategy": fusion_strategy,
    }
    task = run_inference_task.delay(payload)
    return {"task_id": task.id, "status": "queued"}


@router.get('/predict/tasks/{task_id}', response_model=TaskStatusResponse)
async def task_status(task_id: str):
    task = AsyncResult(task_id, app=celery_app)
    result = task.result if task.ready() and not task.failed() else None
    if task.failed():
        raise HTTPException(status_code=500, detail=str(task.result))
    return {"task_id": task_id, "status": task.status.lower(), "result": result}


# ── Explain ───────────────────────────────────────────────────

@router.post('/explain/text')
async def explain_text(text: Optional[str] = Form(None)):
    if text is None:
        raise HTTPException(status_code=400, detail='text is required')
    return await _proxy_ml_service('/explain/text', data={'text': text})


@router.post('/explain/metadata')
async def explain_metadata(
    account_age: Optional[float] = Form(None),
    reviews_per_day: Optional[float] = Form(None),
    verified_purchase_ratio: Optional[float] = Form(None),
    rating_deviation: Optional[float] = Form(None),
    burstiness: Optional[float] = Form(None),
    helpfulness_ratio: Optional[float] = Form(None),
):
    data = {
        'account_age': account_age,
        'reviews_per_day': reviews_per_day,
        'verified_purchase_ratio': verified_purchase_ratio,
        'rating_deviation': rating_deviation,
        'burstiness': burstiness,
        'helpfulness_ratio': helpfulness_ratio,
    }
    return await _proxy_ml_service('/explain/metadata', data=data)


@router.post('/explain/attention')
async def explain_attention(
    text_score: Optional[float] = Form(None),
    meta_score: Optional[float] = Form(None),
):
    data = {'text_score': text_score, 'meta_score': meta_score}
    return await _proxy_ml_service('/explain/attention', data=data)


# ── Flag / Unflag ─────────────────────────────────────────────

@router.post('/reviews/{review_id}/flag')
async def flag_review(
    review_id: int,
    reason: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail='Review not found')
    review.flag_count = (review.flag_count or 0) + 1
    review.flagged = True
    review.last_flagged_at = datetime.utcnow()
    if reason:
        review.flag_reason = reason
    db.add(review)
    audit = AuditLog(
        actor_user_id=getattr(user, 'id', None),
        action='flag_review',
        target_review_id=review.id,
        details=json.dumps({'reason': reason, 'flag_count': review.flag_count}),
    )
    db.add(audit)
    await db.commit()
    await db.refresh(review)
    return {'detail': 'flagged', 'flag_count': review.flag_count}


@router.post('/reviews/{review_id}/unflag')
async def unflag_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    if not getattr(user, 'is_admin', False):
        raise HTTPException(status_code=403, detail='Admin privileges required')
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail='Review not found')
    prev_flag_count = review.flag_count or 0
    prev_reason = review.flag_reason
    review.flagged = False
    review.flag_count = 0
    review.last_flagged_at = None
    review.flag_reason = None
    audit = AuditLog(
        actor_user_id=getattr(user, 'id', None),
        action='unflag_review',
        target_review_id=review.id,
        details=json.dumps({'previous_flag_count': prev_flag_count, 'previous_reason': prev_reason}),
    )
    db.add(review)
    db.add(audit)
    await db.commit()
    await db.refresh(review)
    return {'detail': 'unflagged'}


