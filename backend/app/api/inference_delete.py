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
            'verdict': review.verdict,
            'user_id': review.user_id,
            'text_snippet': (review.text[:200] + '...') if review.text and len(review.text) > 200 else review.text,
        })
    except Exception:
        details = None
    # Create audit log WITHOUT target_review_id to avoid cascade delete
    audit = AuditLog(
        actor_user_id=getattr(user, 'id', None),
        action='delete_review',
        target_review_id=None,  # Set to None to prevent cascade deletion
        details=details,
    )
    db.add(audit)
    await db.flush()  # Flush audit log to DB before deleting review
    # Delete the review using execute + sql_delete
    await db.execute(sql_delete(Review).where(Review.id == review_id))
    await db.commit()
    return {'detail': 'deleted'}
