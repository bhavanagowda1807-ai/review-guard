import React, { useEffect, useState } from 'react'
import { listFlaggedReviews, deleteReview, unflagReview } from '../services/api'
import { ChevronDown, ChevronUp, Sparkles } from 'lucide-react'

function parseReasoning(reasoningStr) {
  if (!reasoningStr) return null
  try { return JSON.parse(reasoningStr) } catch { return null }
}

function ReasonPanel({ reasoning, flagReason }) {
  const r = parseReasoning(reasoning)
  const points = []

  if (flagReason) {
    points.push({ label: '🚩 Flag reason', value: flagReason })
  }

  if (r) {
    // Confidence & probability
    if (r.confidence != null) {
      points.push({ label: '🎯 Fake confidence', value: `${(r.confidence * 100).toFixed(1)}%` })
    }
    if (r.genuine_probability != null) {
      points.push({ label: '✅ Genuine probability', value: `${(r.genuine_probability * 100).toFixed(1)}%` })
    }

    // Modal scores
    const ms = r.modal_scores || {}
    if (ms.text_score != null)     points.push({ label: '📝 Text fake score',     value: (ms.text_score * 100).toFixed(1) + '%' })
    if (ms.metadata_score != null) points.push({ label: '📊 Metadata fake score', value: (ms.metadata_score * 100).toFixed(1) + '%' })

    // Top text signals (LIME words)
    const textWords = (r.top_text_signals || []).filter(s => s.word != null)
    if (textWords.length > 0) {
      points.push({
        label: '🔤 Suspicious words',
        value: textWords.map(s => `"${s.word}" (${s.weight > 0 ? '+' : ''}${s.weight})`).join(', ')
      })
    }

    // Linguistic features
    const ling = r.linguistic
    if (ling) {
      const lingParts = []
      if (ling.superlative_count > 0)   lingParts.push(`${ling.superlative_count} superlatives`)
      if (ling.sentiment_mismatch > 0.1) lingParts.push(`sentiment mismatch: ${ling.sentiment_mismatch?.toFixed(2)}`)
      if (ling.readability > 0)          lingParts.push(`readability: ${ling.readability?.toFixed(1)}`)
      if (ling.pronoun_ratio > 0)        lingParts.push(`pronoun ratio: ${ling.pronoun_ratio?.toFixed(2)}`)
      if (ling.sentence_variance > 0)    lingParts.push(`sentence variance: ${ling.sentence_variance?.toFixed(1)}`)
      if (lingParts.length > 0) points.push({ label: '🔍 Linguistic signals', value: lingParts.join(' · ') })
    }

    // Top SHAP metadata signals
    const topMeta = (r.top_meta_signals || []).slice(0, 3)
    if (topMeta.length > 0) {
      points.push({
        label: '📌 Key metadata signals',
        value: topMeta.map(s => `${s.feature.replace(/_/g, ' ')}: ${s.value}`).join(', ')
      })
    }

    // Attention weights
    const aw = r.attention_weights || {}
    if (aw.text != null && aw.metadata != null) {
      points.push({
        label: '⚖️ Model attention',
        value: `Text ${(aw.text * 100).toFixed(0)}% · Metadata ${(aw.metadata * 100).toFixed(0)}%`
      })
    }

    // Fusion strategy
    if (r.fusion_strategy) {
      points.push({ label: '🔗 Fusion strategy', value: r.fusion_strategy.replace('_', ' ') })
    }
  }

  if (points.length === 0) {
    return (
      <div className="mt-2 text-xs text-slate-200 italic">No detailed reasoning available.</div>
    )
  }

  return (
    <div className="mt-2 rounded bg-rose-950/30 border border-rose-800/30 p-3 space-y-1">
      {points.map((p, i) => (
        <div key={i} className="flex gap-2 text-xs">
          <span className="text-slate-400 min-w-[160px] shrink-0">{p.label}</span>
          <span className="text-rose-200 font-medium">{p.value}</span>
        </div>
      ))}
    </div>
  )
}

export default function AdminFlaggedReviews() {
  const [reviews, setReviews] = useState([])
  const [loading, setLoading] = useState(false)
  const [expandedId, setExpandedId] = useState(null)

  const load = async () => {
    setLoading(true)
    try {
      const data = await listFlaggedReviews(100)
      setReviews(data)
    } catch (err) {
      console.error('Failed to load flagged reviews', err)
      setReviews([])
    } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const handleDelete = async (id) => {
    if (!confirm('Delete this review permanently?')) return
    try {
      await deleteReview(id)
      setReviews(prev => prev.filter(r => r.id !== id))
    } catch (err) {
      console.error('Delete failed', err)
      alert('Delete failed')
    }
  }

  const handleUnflag = async (id) => {
    if (!confirm('Clear flags for this review?')) return
    try {
      await unflagReview(id)
      setReviews(prev => prev.filter(r => r.id !== id))
    } catch (err) {
      console.error('Unflag failed', err)
      alert('Unflag failed')
    }
  }

  const toggleExpand = (id) => setExpandedId(prev => prev === id ? null : id)

  if (!reviews.length) return (
    <div className="rounded border border-[#334155] bg-[#111827] p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="font-semibold">Flagged Reviews</div>
        <div className="text-xs text-slate-200">Admin</div>
      </div>
      <div className="text-sm text-slate-400">No flagged reviews.</div>
    </div>
  )

  return (
    <div className="rounded border border-[#334155] bg-[#111827] p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="font-semibold">Flagged Reviews</div>
        <div className="text-xs text-slate-200">Admin</div>
      </div>
      <div className="space-y-2">
        {reviews.map(review => (
          <div key={review.id} className="rounded bg-[#1f2937] p-3 text-sm">
            <div className="flex items-center justify-between gap-3">
              <span className={review.verdict === 'fake' ? 'text-rose-300' : 'text-emerald-300'}>
                {review.verdict || 'n/a'}
              </span>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs text-slate-400">Flags: {review.flag_count || 0}</span>
                <button
                  onClick={() => toggleExpand(review.id)}
                  className="flex items-center gap-1 text-xs rounded bg-violet-600/20 px-2 py-1 text-violet-300 hover:bg-violet-600/30 transition-colors"
                >
                  <Sparkles size={11} />
                  Explain
                  {expandedId === review.id ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
                </button>
                <button onClick={() => handleUnflag(review.id)} className="text-xs rounded bg-amber-600/20 px-2 py-1 text-amber-300">Unflag</button>
                <button onClick={() => handleDelete(review.id)} className="text-xs rounded bg-red-600/20 px-2 py-1 text-rose-300">Delete</button>
              </div>
            </div>
            <div className="mt-1 truncate text-xs text-slate-400">{review.text || 'Image/metadata-only review'}</div>
            {expandedId === review.id && (
              <ReasonPanel reasoning={review.reasoning} flagReason={review.flag_reason} />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
