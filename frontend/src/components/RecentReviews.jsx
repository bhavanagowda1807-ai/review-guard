import React, {useEffect, useState} from 'react'
import {listReviews} from '../services/api'

export default function RecentReviews({refreshKey}){
  const [reviews, setReviews] = useState([])

  useEffect(() => {
    let alive = true
    listReviews(8)
      .then(data => { if (alive) setReviews(data) })
      .catch(() => { if (alive) setReviews([]) })
    return () => { alive = false }
  }, [refreshKey])

  return (
    <div className="rounded border border-[#334155] bg-[#111827] p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="font-semibold">Recent Predictions</div>
        <div className="text-xs text-slate-200">PostgreSQL</div>
      </div>
      {!reviews.length && <div className="text-sm text-slate-400">No stored predictions yet.</div>}
      <div className="space-y-2">
        {reviews.map(review => (
          <div key={review.id} className="rounded bg-[#1f2937] p-3 text-sm">
            <div className="flex items-center justify-between gap-3">
              <span className={review.verdict === 'fake' ? 'text-rose-300' : 'text-emerald-300'}>{review.verdict || 'pending'}</span>
              <span className="text-xs text-slate-400">{review.confidence ? `${(review.confidence * 100).toFixed(1)}%` : 'n/a'}</span>
            </div>
            <div className="mt-1 truncate text-xs text-slate-400">{review.text || 'Image/metadata-only review'}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
