import React, { useState } from 'react'
import { Loader2, ShieldCheck, Sparkles } from 'lucide-react'
import {
  predictReview,
  predictReviewAsync,
  getPredictionTask,
  explainText,
  explainMetadata,
  explainAttention,
} from '../services/api'
import ResultCard from './ResultCard'
import ModalityCard from './ModalityCard'
import AttentionViz from './AttentionViz'
import ROCChart from './ROCChart'
import ExplainabilityPanel from './ExplainabilityPanel'
import RecentReviews from './RecentReviews'
import AdminFlaggedReviews from './AdminFlaggedReviews'
import AdminAuditLogs from './AdminAuditLogs'
import ModelStatus from './ModelStatus'

export default function UploadAdvanced() {
  const [text, setText] = useState('')
  const [result, setResult] = useState(null)
  const [explainability, setExplainability] = useState(null)
  const [loading, setLoading] = useState(false)
  const [showExplain, setShowExplain] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)
  const [useAsync, setUseAsync] = useState(false)
  const [taskStatus, setTaskStatus] = useState(null)
  const [metadata, setMetadata] = useState({
    rating: 5,
    account_age: 120,
    reviews_per_day: 0.4,
    verified_purchase_ratio: 0.75,
    rating_deviation: 0.3,
    burstiness: 0.4,
    helpfulness_ratio: 0.55,
    similarity_score: 0.0,
    sentiment_rating_mismatch: 0.0,
    night_review_ratio: 0.0,
    reviewer_overlap_score: 0.0,
    fusion_strategy: 'attention',
  })

  const setMeta = (key, value) => setMetadata(prev => ({ ...prev, [key]: value }))

  const submit = async (e) => {
    e.preventDefault()
    const form = new FormData()
    form.append('text', text)
    Object.entries(metadata).forEach(([key, value]) => form.append(key, value))
    setLoading(true)
    try {
      let res
      if (useAsync) {
        const task = await predictReviewAsync(form)
        setTaskStatus(`Queued ${task.task_id}`)
        for (let i = 0; i < 30; i++) {
          const status = await getPredictionTask(task.task_id)
          setTaskStatus(status.status)
          if (status.result) { res = status.result; break }
          await new Promise(r => setTimeout(r, 1000))
        }
        if (!res) throw new Error('Async inference timed out')
      } else {
        res = await predictReview(form)
      }
      setResult(res)
      setExplainability(null)
      setShowExplain(false)
      setRefreshKey(v => v + 1)
      setTaskStatus(null)
    } catch (err) {
      console.error(err)
      alert('Inference failed. Check that backend, Redis worker, and ML service are running.')
    } finally {
      setLoading(false)
    }
  }

  const requestExplanations = async () => {
    if (!result) return
    const explain = {}
    try { explain.lime = await explainText(text) } catch (err) { console.error('LIME failed', err) }
    try { explain.shap = await explainMetadata(metadata) } catch (err) { console.error('SHAP failed', err) }
    try {
      explain.attention = await explainAttention(
        result.modal_scores?.text,
        result.modal_scores?.meta,
      )
    } catch (err) { console.error('Attention failed', err) }
    setExplainability(explain)
    setShowExplain(true)
  }

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-[420px_1fr]">
      {/* ── Input form ── */}
      <form onSubmit={submit} className="space-y-5 rounded border border-[#334155] bg-[#111827] p-4">
        <div>
          <label className="mb-2 block text-sm font-medium text-slate-300">Review text</label>
          <textarea
            value={text}
            onChange={e => setText(e.target.value)}
            className="min-h-40 w-full resize-y rounded border border-[#334155] bg-[#111827] p-3 text-sm outline-none focus:border-indigo-400"
            rows={8}
            placeholder="Paste an e-commerce review…"
          />
        </div>

        {/* Metadata sliders */}
        <div>
          <label className="mb-2 block text-sm font-medium text-slate-300">Reviewer metadata</label>
          <div className="grid grid-cols-2 gap-3">
            {[
              ['rating', 'Rating', 1, 5, 0.5],
              ['account_age', 'Account age (days)', 0, 730, 1],
              ['reviews_per_day', 'Reviews / day', 0, 8, 0.1],
              ['verified_purchase_ratio', 'Verified ratio', 0, 1, 0.05],
              ['rating_deviation', 'Rating deviation', 0, 3, 0.1],
              ['burstiness', 'Burstiness', 0, 8, 0.1],
              ['helpfulness_ratio', 'Helpful ratio', 0, 1, 0.05],
              ['similarity_score', 'Review similarity', 0, 1, 0.05],
              ['sentiment_rating_mismatch', 'Sentiment mismatch', 0, 1, 0.05],
              ['night_review_ratio', 'Night-time ratio', 0, 1, 0.05],
              ['reviewer_overlap_score', 'Reviewer overlap', 0, 1, 0.05],
            ].map(([key, label, min, max, step]) => (
              <label key={key} className="text-sm text-slate-300">
                <span className="mb-1 block">{label}</span>
                <input
                  type="number" min={min} max={max} step={step}
                  value={metadata[key]}
                  onChange={e => setMeta(key, e.target.value)}
                  className="w-full rounded border border-[#334155] bg-[#111827] px-2 py-2 outline-none focus:border-indigo-400"
                />
              </label>
            ))}
            <label className="text-sm text-slate-300">
              <span className="mb-1 block">Fusion strategy</span>
              <select
                value={metadata.fusion_strategy}
                onChange={e => setMeta('fusion_strategy', e.target.value)}
                className="w-full rounded border border-[#334155] bg-[#111827] px-2 py-2 outline-none focus:border-indigo-400"
              >
                <option value="attention">Attention</option>
                <option value="late">Late fusion</option>
              </select>
            </label>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <label className="inline-flex items-center gap-2 rounded border border-[#334155] px-3 py-2 text-sm text-slate-300">
            <input type="checkbox" checked={useAsync} onChange={e => setUseAsync(e.target.checked)} />
            Async
          </label>
          <button
            disabled={loading}
            className="inline-flex items-center gap-2 rounded bg-indigo-500 px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <ShieldCheck size={16} />}
            {loading ? 'Analyzing…' : 'Analyze'}
          </button>
          {result && (
            <button
              type="button"
              onClick={requestExplanations}
              className="inline-flex items-center gap-2 rounded bg-fuchsia-500 px-4 py-2 text-sm font-medium text-white"
            >
              <Sparkles size={16} /> Explain
            </button>
          )}
        </div>
        {taskStatus && (
          <div className="rounded bg-[#1f2937] p-2 text-xs text-slate-400">Task: {taskStatus}</div>
        )}
      </form>

      {/* ── Results panel ── */}
      <div className="grid grid-cols-1 gap-4">
        <ModelStatus />

        {result ? (
          <ResultCard
            verdict={result.verdict}
            confidence={result.confidence}
            genuineProbability={result.genuine_probability}
            strategy={result.fusion_strategy}
          />
        ) : (
          <div className="rounded border border-[#334155] bg-[#111827] p-5 text-slate-400">
            Run an analysis to see the verdict, modality scores, attention weights, and ROC comparison.
          </div>
        )}

        {/* Text + Metadata modality cards only */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <ModalityCard
            title="Text"
            score={result?.modal_scores?.text}
            details={result?.modal_details?.text}
            features={result?.text_features}
          />
          <ModalityCard
            title="Metadata"
            score={result?.modal_scores?.meta}
            details={result?.modal_details?.meta}
            features={result?.metadata_features}
          />
        </div>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <AttentionViz attention={result?.attention} />
          <ROCChart curves={result?.roc_curves} />
        </div>

        {showExplain && <ExplainabilityPanel explainability={explainability} />}
        <AdminFlaggedReviews />
        <AdminAuditLogs />
        <RecentReviews refreshKey={refreshKey} />
      </div>
    </div>
  )
}
