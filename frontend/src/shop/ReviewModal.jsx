import React, { useEffect, useState } from 'react'
import { apiFetch, authHeaders, API_BASE } from './shopApi'

export default function ReviewModal({ product, user, setPage, onClose }) {
  const [reviews, setReviews] = useState([])
  const [loading, setLoading] = useState(false)
  const [pageNum, setPageNum] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const REVIEWS_PER_PAGE = 8
  const [rating, setRating] = useState(5)
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [done, setDone] = useState(false)
  const [detectionResult, setDetectionResult] = useState(null)
  const [showExplanation, setShowExplanation] = useState(false)

  function buildExplanationPoints(result) {
    if (!result) return []
    const points = []
    const confidence = result.confidence ?? 0
    const genuineProb = result.genuine_probability ?? 0.5
    const ms = result.modal_scores || {}
    const attention = result.attention || {}
    const textFeatures = result.text_features || {}
    const metaFeatures = result.metadata_features || {}

    points.push({
      label: result.verdict === 'fake' ? '⚠️ Verdict' : '✅ Verdict',
      value: result.verdict === 'fake' ? 'Suspicious / Fake' : 'Looks Genuine',
      highlight: result.verdict === 'fake',
    })
    points.push({
      label: '🎯 Confidence',
      value: `${(confidence * 100).toFixed(1)}%`,
    })
    points.push({
      label: '✅ Genuine probability',
      value: `${(genuineProb * 100).toFixed(1)}%`,
    })
    if (ms.text != null) points.push({
      label: '📝 Text signal',
      value: `${(ms.text * 100).toFixed(1)}% genuine`,
    })
    if (ms.meta != null) points.push({
      label: '📊 Metadata signal',
      value: `${(ms.meta * 100).toFixed(1)}% genuine`,
    })
    if (attention.text != null && attention.meta != null) points.push({
      label: '⚖️ Model attention',
      value: `Text ${(attention.text * 100).toFixed(0)}% · Metadata ${(attention.meta * 100).toFixed(0)}%`,
    })

    // Linguistic signals
    const lingParts = []
    if (textFeatures.superlative_count > 0) lingParts.push(`${textFeatures.superlative_count} superlative${textFeatures.superlative_count > 1 ? 's' : ''}`)
    if (textFeatures.sentiment_mismatch > 0.3) lingParts.push(`sentiment mismatch: ${textFeatures.sentiment_mismatch.toFixed(2)}`)
    if (textFeatures.readability != null) lingParts.push(`readability: ${textFeatures.readability.toFixed(1)}`)
    if (textFeatures.pronoun_ratio != null) lingParts.push(`pronoun ratio: ${textFeatures.pronoun_ratio.toFixed(2)}`)
    if (lingParts.length > 0) points.push({ label: '🔍 Linguistic signals', value: lingParts.join(' · ') })

    // Metadata signals
    const metaParts = []
    if (metaFeatures.account_age != null) metaParts.push(`Account age: ${metaFeatures.account_age}d`)
    if (metaFeatures.reviews_per_day != null) metaParts.push(`Reviews/day: ${metaFeatures.reviews_per_day}`)
    if (metaFeatures.burstiness != null) metaParts.push(`Burstiness: ${metaFeatures.burstiness}`)
    if (metaParts.length > 0) points.push({ label: '👤 Reviewer signals', value: metaParts.join(' · ') })

    if (result.fusion_strategy) points.push({
      label: '🔗 Fusion strategy',
      value: result.fusion_strategy.replace('_', ' '),
    })

    return points
  }

  useEffect(() => { 
    setReviews([])
    setPageNum(0)
    setHasMore(true)
    loadReviews(0)
  }, [product?.id])

  async function loadReviews(page = 0) {
    if (!product?.id) return
    setLoading(true)
    try {
      const allReviews = await apiFetch(`/api/shop/products/${product.id}/reviews`)
      const start = page * REVIEWS_PER_PAGE
      const end = start + REVIEWS_PER_PAGE
      const pageReviews = allReviews.slice(start, end)
      
      if (page === 0) {
        setReviews(pageReviews)
      } else {
        setReviews(prev => [...prev, ...pageReviews])
      }
      setHasMore(end < allReviews.length)
    } catch { 
      if (page === 0) setReviews([])
    }
    setLoading(false)
  }

  async function submit() {
    if (!body.trim() || !user) return
    setSubmitting(true)
    setDetectionResult(null)
    try {
      // Auto-fetch user metadata for ML classifier
      let meta = {}
      try { meta = await apiFetch('/api/shop/user/metadata') } catch {}

      const fd = new FormData()
      fd.append('text', `${title ? title + '. ' : ''}${body}`)
      fd.append('rating', rating)
      fd.append('fusion_strategy', 'attention')
      if (product?.id) fd.append('product_id', product.id)
      fd.append('account_age',                meta.account_age                ?? 30)
      fd.append('reviews_per_day',            meta.reviews_per_day            ?? 0.1)
      fd.append('verified_purchase_ratio',    meta.verified_purchase_ratio    ?? 0.5)
      fd.append('rating_deviation',           meta.rating_deviation           ?? 0.5)
      fd.append('burstiness',                 meta.burstiness                 ?? 0.5)
      fd.append('helpfulness_ratio',          meta.helpfulness_ratio          ?? 0.3)
      fd.append('similarity_score',           meta.similarity_score           ?? 0.0)
      fd.append('sentiment_rating_mismatch',  meta.sentiment_rating_mismatch  ?? 0.0)
      fd.append('night_review_ratio',         meta.night_review_ratio         ?? 0.0)
      fd.append('reviewer_overlap_score',     meta.reviewer_overlap_score     ?? 0.0)

      const response = await fetch(`${API_BASE}/api/predict`, { method: 'POST', headers: authHeaders(), body: fd })
      const result = await response.json()
      setDetectionResult(result)
      setShowExplanation(true)

      // Reload reviews list after a short delay
      setTimeout(() => {
        setDone(true)
        setPageNum(0)
        setHasMore(true)
        loadReviews(0)
      }, 1500)
    } catch {}
    setSubmitting(false)
  }

  const getConfidenceBadge = (review) => {
    const confidence = review.confidence || 0
    const genuineProb = review.genuine_probability || 0.5
    
    if (review.verdict === 'genuine' && confidence > 0.7) {
      return {
        bg: 'bg-emerald-50 border-emerald-200',
        text: 'text-emerald-700',
        icon: '✓',
        label: 'AI Verified',
        score: Math.round(genuineProb * 100)
      }
    } else if (review.verdict === 'fake' && confidence > 0.7) {
      return {
        bg: 'bg-red-50 border-red-200',
        text: 'text-red-700',
        icon: '⚠',
        label: 'AI Flagged',
        score: Math.round((1 - genuineProb) * 100)
      }
    } else {
      return {
        bg: 'bg-amber-50 border-amber-200',
        text: 'text-amber-700',
        icon: '⚡',
        label: 'Reviewing',
        score: Math.round(confidence * 100)
      }
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white">
          <div>
            <div className="font-bold text-slate-800 text-lg">{product?.name}</div>
            <div className="flex items-center gap-2 mt-1">
              <div className="text-xs text-slate-400">{product?.category}</div>
              <span className="text-slate-300">•</span>
              <div className="flex items-center gap-1 text-xs">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></span>
                <span className="text-blue-600 font-semibold">ReviewGuard Protected</span>
              </div>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-2xl w-8 h-8 flex items-center justify-center rounded-lg hover:bg-slate-100 transition">×</button>
        </div>

        {/* Existing reviews - Paginated */}
        <div className="max-h-96 overflow-y-auto px-6 py-4 border-b border-slate-100 bg-slate-50/30">
          {reviews.length === 0 && !loading
            ? <div className="text-slate-400 text-sm text-center py-10">
                <div className="text-4xl mb-3">💬</div>
                <div className="font-semibold">No reviews yet</div>
                <div className="text-xs mt-1">Be the first to share your experience!</div>
              </div>
            : (
              <>
                {reviews.map(r => {
                  const badge = getConfidenceBadge(r)
                  return (
                    <div key={r.id} className={`mb-3 rounded-xl p-4 border-2 transition-all hover:shadow-md ${badge.bg}`}>
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-yellow-500 text-sm font-bold">{'★'.repeat(r.rating || 0)}</span>
                            <span className="text-slate-400 text-xs">• {r.username || 'Anonymous'}</span>
                          </div>
                        </div>
                        <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold ${badge.bg} ${badge.text} border whitespace-nowrap`}>
                          <span>{badge.icon}</span>
                          <span>{badge.label}</span>
                          <span className="text-[10px] opacity-70">{badge.score}%</span>
                        </div>
                      </div>
                      <p className="text-sm text-slate-700 leading-relaxed">{r.text}</p>
                      
                      {/* Explainability hint */}
                      {r.verdict && r.confidence > 0.6 && (
                        <div className="mt-3 pt-3 border-t border-slate-200/50">
                          <div className="flex items-center gap-1 text-[11px] text-slate-500">
                            <span>🔍</span>
                            <span>Analyzed by multimodal ML • Text + Metadata + Behavioral patterns</span>
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })}
                
                {hasMore && (
                  <div className="text-center py-4">
                    <button
                      onClick={() => {
                        const nextPage = pageNum + 1
                        setPageNum(nextPage)
                        loadReviews(nextPage)
                      }}
                      disabled={loading}
                      className="px-4 py-2 text-sm bg-slate-200 hover:bg-slate-300 text-slate-700 font-semibold rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {loading ? 'Loading...' : 'Load More Reviews'}
                    </button>
                  </div>
                )}
              </>
            )
          }
        </div>

        {/* Real-time AI Explanation Panel */}
        {detectionResult && showExplanation && (() => {
          const isFake = detectionResult.verdict === 'fake'
          const points = buildExplanationPoints(detectionResult)
          return (
            <div className={`px-6 py-5 border-b ${isFake ? 'bg-red-50 border-red-100' : 'bg-emerald-50 border-emerald-100'}`}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-xl">{isFake ? '⚠️' : '✅'}</span>
                  <span className={`font-bold text-sm ${isFake ? 'text-red-700' : 'text-emerald-700'}`}>
                    AI Analysis — {isFake ? 'Suspicious Pattern Detected' : 'Looks Genuine'}
                  </span>
                </div>
                <button
                  onClick={() => setShowExplanation(false)}
                  className="text-slate-400 hover:text-slate-600 text-lg w-6 h-6 flex items-center justify-center rounded hover:bg-black/5 transition"
                >×</button>
              </div>

              {/* Confidence bar */}
              <div className="flex items-center gap-2 mb-4">
                <div className="flex-1 h-2 bg-white/70 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ${isFake ? 'bg-red-500' : 'bg-emerald-500'}`}
                    style={{ width: `${(detectionResult.confidence || 0) * 100}%` }}
                  />
                </div>
                <span className={`text-xs font-bold ${isFake ? 'text-red-600' : 'text-emerald-600'}`}>
                  {Math.round((detectionResult.confidence || 0) * 100)}% confident
                </span>
              </div>

              {/* Explanation points */}
              <div className="space-y-1.5">
                {points.map((p, i) => (
                  <div key={i} className="flex gap-3 text-xs">
                    <span className="text-slate-500 min-w-[160px] shrink-0">{p.label}</span>
                    <span className={`font-medium ${p.highlight ? 'text-red-600' : 'text-slate-700'}`}>{p.value}</span>
                  </div>
                ))}
              </div>

              <div className="mt-3 pt-3 border-t border-black/5 text-[10px] text-slate-400 flex items-center gap-1">
                <span>🔒</span>
                <span>Powered by multimodal ML — text encoder + behavioral metadata + attention fusion</span>
              </div>
            </div>
          )
        })()}

        {/* Write review form — owners cannot review their own products */}
        {user && user.role !== 'Owner' ? (
          <div className="px-6 py-5 bg-white">
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm font-bold text-slate-700">Write a Review</div>
              <div className="text-[10px] text-slate-400 flex items-center gap-1">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-green-500"></span>
                AI monitoring active
              </div>
            </div>
            <div className="flex gap-1 mb-3">
              {[1, 2, 3, 4, 5].map(n => (
                <button key={n} onClick={() => setRating(n)}
                  className={`text-2xl transition-all ${n <= rating ? 'text-yellow-400 scale-110' : 'text-slate-300 hover:text-yellow-200 hover:scale-105'}`}>★</button>
              ))}
            </div>
            <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Review title (optional)"
              className="w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-lg mb-2 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 transition" />
            <textarea value={body} onChange={e => setBody(e.target.value)} rows={3}
              placeholder="Share your honest experience with this product..."
              className="w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-lg mb-3 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 resize-none transition" />
            {done && (
              <div className="text-xs text-green-700 bg-green-50 border border-green-200 rounded-lg px-4 py-3 mb-3 flex items-start gap-2">
                <span className="text-lg">✓</span>
                <div>
                  <div className="font-bold mb-0.5">Review submitted successfully!</div>
                  <div className="text-green-600">Your review has been analyzed and published.</div>
                </div>
              </div>
            )}
            <button onClick={submit} disabled={submitting || !body.trim() || done}
              className="w-full py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold rounded-xl text-sm transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2">
              {submitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  <span>Analyzing with AI...</span>
                </>
              ) : (
                <>
                  <span>🛡️</span>
                  <span>Submit Review</span>
                </>
              )}
            </button>
            <div className="text-[11px] text-slate-500 text-center mt-2 flex items-center justify-center gap-1">
              <span>🔒</span>
              <span>Protected by ReviewGuard multimodal AI detection</span>
            </div>
          </div>
        ) : (
          <div className="px-6 py-6 text-center">
            <div className="text-slate-400 text-sm mb-3">Sign in to write a review</div>
            <button onClick={() => setPage('auth')} className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm rounded-lg transition">Sign In</button>
          </div>
        )}
      </div>
    </div>
  )
}
