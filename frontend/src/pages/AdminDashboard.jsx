import React, { useEffect, useState, useRef } from 'react'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function authHeaders() {
  const token = localStorage.getItem('fake_review_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export default function AdminDashboard({ user, navigate }) {
  const [tab, setTab] = useState('overview')
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [reviews, setReviews] = useState([])
  const [auditLogs, setAuditLogs] = useState([])
  const [batches, setBatches] = useState([])
  const [msg, setMsg] = useState('')
  const [msgType, setMsgType] = useState('ok') // 'ok' | 'err'
  const [csvFile, setCsvFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState(null)
  const [uploadProgress, setUploadProgress] = useState(null) // { batchId, done, total, status }
  const uploadPollRef = useRef(null)
  const deletedIdsRef = useRef(new Set())
  const [deletingId, setDeletingId] = useState(null)
  const [clearingAll, setClearingAll] = useState(false)
  const [confirmClear, setConfirmClear] = useState(false)
  const [reviewPage, setReviewPage] = useState(1)
  const [reviewFilter, setReviewFilter] = useState('all') // 'all' | 'fake' | 'genuine' | 'pending'
  const fileRef = useRef()
  const PAGE_SIZE = 50
  const [expandedReviewId, setExpandedReviewId] = React.useState(null)

  function parseReasoning(str) {
    if (!str) return null
    try { return JSON.parse(str) } catch { return null }
  }

  function getReasonPoints(r) {
    const points = []
    const rr = parseReasoning(r.reasoning)
    if (r.flag_reason) points.push({ label: '🚩 Flag reason', value: r.flag_reason })
    if (rr) {
      if (rr.confidence != null) points.push({ label: '🎯 Fake confidence', value: `${(rr.confidence * 100).toFixed(1)}%` })
      if (rr.genuine_probability != null) points.push({ label: '✅ Genuine probability', value: `${(rr.genuine_probability * 100).toFixed(1)}%` })
      const ms = rr.modal_scores || {}
      if (ms.text_score != null) points.push({ label: '📝 Text fake score', value: `${((1 - ms.text_score) * 100).toFixed(1)}%` })
      if (ms.metadata_score != null) points.push({ label: '📊 Metadata fake score', value: `${((1 - ms.metadata_score) * 100).toFixed(1)}%` })
      const ling = rr.linguistic || {}
      const lingParts = []
      if (ling.superlative_count > 0) lingParts.push(`${ling.superlative_count} superlative${ling.superlative_count > 1 ? 's' : ''}`)
      if (ling.sentiment_mismatch > 0.5) lingParts.push(`sentiment mismatch: ${ling.sentiment_mismatch.toFixed(2)}`)
      if (ling.readability != null) lingParts.push(`readability: ${ling.readability.toFixed(1)}`)
      if (ling.pronoun_ratio != null) lingParts.push(`pronoun ratio: ${ling.pronoun_ratio.toFixed(2)}`)
      if (lingParts.length > 0) points.push({ label: '🔍 Linguistic signals', value: lingParts.join(' · ') })
      const topMeta = rr.top_meta_signals || []
      if (topMeta.length > 0) {
        // Show account info first
        const accountFields = topMeta.filter(s => ['Account Age (days)', 'Reviews Per Day', 'Verified Purchase Ratio'].includes(s.feature))
        const behaviorFields = topMeta.filter(s => !['Account Age (days)', 'Reviews Per Day', 'Verified Purchase Ratio'].includes(s.feature))
        if (accountFields.length > 0) points.push({ label: '👤 Reviewer info', value: accountFields.map(s => `${s.feature}: ${s.value}`).join(' · ') })
        if (behaviorFields.length > 0) points.push({ label: '📌 Behavior signals', value: behaviorFields.map(s => `${s.feature}: ${s.value}`).join(' · ') })
      }
      const aw = rr.attention_weights || {}
      if (aw.text != null && aw.metadata != null) points.push({ label: '⚖️ Model attention', value: `Text ${(aw.text * 100).toFixed(0)}% · Metadata ${(aw.metadata * 100).toFixed(0)}%` })
      if (rr.fusion_strategy) points.push({ label: '🔗 Fusion strategy', value: rr.fusion_strategy.replace('_', ' ') })
    }
    return points
  }


  useEffect(() => {
    if (!user?.is_admin) { navigate('/reviewguard/login'); return }
    fetchAll()
  }, [user])

  useEffect(() => { fetchReviews() }, [reviewPage, reviewFilter])

  // Real-time polling — refresh reviews and stats every 8 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchReviews()
      fetchStats()
    }, 8000)
    return () => clearInterval(interval)
  }, [reviewPage, reviewFilter])

  async function fetchAll() {
    fetchStats(); fetchUsers(); fetchReviews()
    fetchAuditLogs(); fetchBatches()
  }

  async function fetchStats() {
    const res = await fetch(`${API}/api/shop/stats/reviews`, { headers: authHeaders() })
    if (res.ok) setStats(await res.json())
  }

  async function fetchUsers() {
    const res = await fetch(`${API}/api/admin/users`, { headers: authHeaders() })
    if (res.ok) setUsers(await res.json())
  }

  async function fetchReviews() {
    const skip = (reviewPage - 1) * PAGE_SIZE
    let url = `${API}/api/reviews?limit=${PAGE_SIZE}&skip=${skip}`
    if (reviewFilter !== 'all') url += `&verdict=${reviewFilter}`
    const res = await fetch(url, { headers: authHeaders() })
    if (res.ok) {
      const data = await res.json()
      setReviews(data.filter(r => !deletedIdsRef.current.has(r.id)))
    }
  }

  async function fetchAuditLogs() {
    try {
      const res = await fetch(`${API}/api/audit?page=1&page_size=100`, { headers: authHeaders() })
      if (res.ok) {
        const d = await res.json()
        setAuditLogs(d.items || [])
      } else {
        const err = await res.text()
        console.error('Audit log fetch failed:', res.status, err)
        setAuditLogs([{ id: 0, action: `Error ${res.status}: ${err}`, created_at: new Date().toISOString() }])
      }
    } catch (e) {
      console.error('Audit log error:', e)
      setAuditLogs([{ id: 0, action: `Network error: ${e.message}`, created_at: new Date().toISOString() }])
    }
  }

  async function fetchBatches() {
    const res = await fetch(`${API}/api/shop/upload/batches`, { headers: authHeaders() })
    if (res.ok) setBatches(await res.json())
  }

  async function uploadCSV() {
    if (!csvFile) return
    setUploading(true)
    setUploadResult(null)
    setUploadProgress(null)

    const fd = new FormData()
    fd.append('csv_file', csvFile)

    try {
      const res = await fetch(`${API}/api/shop/upload/reviews`, {
        method: 'POST', headers: authHeaders(), body: fd
      })
      const data = await res.json()

      if (!res.ok) {
        setUploadResult({ error: data.detail })
        setUploading(false)
        return
      }

      // Server returns immediately — start polling for progress
      setCsvFile(null)
      if (fileRef.current) fileRef.current.value = ''

      const { batch_id, total_rows } = data
      setUploadProgress({ batchId: batch_id, done: 0, total: total_rows || 0, status: 'processing' })

      // Clear any previous poll
      if (uploadPollRef.current) clearInterval(uploadPollRef.current)

      uploadPollRef.current = setInterval(async () => {
        try {
          const pr = await fetch(`${API}/api/shop/upload/batches/${batch_id}`, { headers: authHeaders() })
          if (!pr.ok) {
            // Batch not found — stop polling
            clearInterval(uploadPollRef.current)
            uploadPollRef.current = null
            setUploading(false)
            setUploadProgress(null)
            fetchBatches(); fetchReviews(); fetchStats()
            return
          }
          const batch = await pr.json()
          setUploadProgress({
            batchId: batch_id,
            done: batch.success_rows + batch.failed_rows,
            total: batch.total_rows,
            status: batch.status,
            success: batch.success_rows,
            failed: batch.failed_rows,
          })

          if (batch.status === 'completed' || batch.status === 'failed') {
            clearInterval(uploadPollRef.current)
            uploadPollRef.current = null
            setUploading(false)
            fetchBatches(); fetchReviews(); fetchStats()
          }
        } catch (_) {}
      }, 2000) // poll every 2 seconds

    } catch (err) {
      setUploadResult({ error: 'Upload failed — ' + err.message })
      setUploading(false)
    }
  }

  async function handleDeleteReview(id) {
    setDeletingId(id)
    const res = await fetch(`${API}/api/reviews/${id}`, {
      method: 'DELETE',
      headers: authHeaders()
    })
    if (res.ok) {
      deletedIdsRef.current.add(id)
      setReviews(prev => prev.filter(r => r.id !== id))
      flash('Review deleted ✓', 'ok')
      fetchStats()
    } else {
      let errMsg = 'Delete failed'
      try { const e = await res.json(); errMsg = e.detail || errMsg } catch {}
      flash(errMsg, 'err')
    }
    setDeletingId(null)
  }

  async function clearAllReviews() {
    setClearingAll(true)
    setConfirmClear(false)
    try {
      const res = await fetch(`${API}/api/reviews`, { method: 'DELETE', headers: authHeaders() })
      if (res.ok) {
        const data = await res.json()
        deletedIdsRef.current.clear()
        flash(data.detail || 'Dataset cleared', 'ok')
      } else {
        flash('Clear failed', 'err')
      }
    } catch (e) {
      flash('Clear failed: ' + e.message, 'err')
    }
    setClearingAll(false)
    fetchReviews(); fetchStats()
  }

  async function backfillReasoning() {
    flash('Backfilling reasoning for existing reviews...', 'ok')
    try {
      const res = await fetch(`${API}/api/reviews/backfill-reasoning`, { method: 'POST', headers: authHeaders() })
      const data = await res.json()
      flash(data.detail || 'Backfill complete', res.ok ? 'ok' : 'err')
      fetchReviews()
    } catch (e) {
      flash('Backfill failed: ' + e.message, 'err')
    }
  }

  async function updateUserRole(userId, role) {
    const res = await fetch(`${API}/api/admin/users/${userId}/role`, {
      method: 'PATCH', headers: { ...authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ role })
    })
    if (res.ok) { fetchUsers(); flash('Role updated ✓', 'ok') }
  }

  async function toggleUserActive(userId, isActive) {
    const res = await fetch(`${API}/api/admin/users/${userId}/active`, {
      method: 'PATCH', headers: { ...authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_active: !isActive })
    })
    if (res.ok) { fetchUsers(); flash('User updated ✓', 'ok') }
  }

  function flash(m, type = 'ok') {
    setMsg(m); setMsgType(type)
    setTimeout(() => setMsg(''), 3000)
  }

  const tabs = [
    { id: 'overview', label: '📊 Overview' },
    { id: 'upload', label: '📤 CSV Upload' },
    { id: 'reviews', label: '📝 All Reviews' },
    { id: 'users', label: '👥 Users' },
    { id: 'audit', label: '📋 Audit Log' },
  ]

  if (!user?.is_admin) return (
    <div className="min-h-screen bg-[#111827] flex items-center justify-center text-slate-400">Access denied.</div>
  )

  return (
    <div className="min-h-screen bg-[#111827] text-slate-100">
      {/* Header */}
      <div className="border-b border-[#1e3a5f]/40 bg-[#111827] px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold">⚙️ Admin Dashboard</h1>
            <p className="text-sm text-slate-400">Full control — users, reviews, uploads, audit logs</p>
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            {msg && (
              <span className={`text-sm font-medium ${msgType === 'err' ? 'text-red-400' : 'text-slate-400'}`}>{msg}</span>
            )}
            <button onClick={() => navigate('/reviewguard')} className="text-sm text-slate-400 hover:text-slate-400 px-3 py-1.5 rounded-lg hover:bg-[#1e3a5f]/50 transition">🛡️ AI Detection</button>
            <button onClick={() => navigate('/admin/charts')} className="text-sm text-slate-400 hover:text-purple-400 px-3 py-1.5 rounded-lg hover:bg-[#1e3a5f]/50 transition">📊 Analytics</button>
            <span className="text-sm text-slate-400">👑 {user.username}</span>
            <button onClick={() => { localStorage.removeItem('fake_review_token'); navigate('/') }} className="text-xs bg-[#1e3a5f] hover:bg-[#1e3a5f] px-3 py-1.5 rounded-lg transition">Logout</button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6">
        {/* Tabs */}
        <div className="flex gap-1 bg-[#111827]/30 rounded-xl p-1 mb-6 flex-wrap">
          {tabs.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${tab === t.id ? 'bg-[#3b82f6] text-white' : 'text-slate-400 hover:text-slate-200'}`}>
              {t.label}
            </button>
          ))}
        </div>

        {/* ── OVERVIEW ── */}
        {tab === 'overview' && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[
                { label: 'Total Reviews', value: stats?.total ?? '—', color: 'text-slate-200' },
                { label: 'Genuine', value: stats?.genuine ?? '—', color: 'text-slate-400' },
                { label: 'Fake', value: stats?.fake ?? '—', color: 'text-red-400' },
                { label: 'Users', value: users.length, color: 'text-blue-400' },
                { label: 'Upload Batches', value: batches.length, color: 'text-purple-400' },
                { label: 'Audit Events', value: auditLogs.length, color: 'text-slate-200' },
                { label: 'Fake Rate', value: stats?.total ? `${((stats.fake / stats.total) * 100).toFixed(1)}%` : '—', color: 'text-orange-400' },
                { label: 'Genuine Rate', value: stats?.total ? `${((stats.genuine / stats.total) * 100).toFixed(1)}%` : '—', color: 'text-slate-300' },
              ].map(s => (
                <div key={s.label} className="bg-[#111827] border border-[#1e3a5f]/40 rounded-xl p-4">
                  <div className={`text-3xl font-bold ${s.color}`}>{s.value}</div>
                  <div className="text-sm text-slate-300/50 mt-1">{s.label}</div>
                </div>
              ))}
            </div>

            {/* Bar chart */}
            {stats?.by_product?.length > 0 && (
              <div className="bg-[#111827] border border-[#1e3a5f]/40 rounded-xl p-5">
                <h2 className="font-medium mb-4">Authenticity by Product</h2>
                <div className="space-y-3">
                  {stats.by_product.map(p => (
                    <div key={p.product} className="flex items-center gap-4 text-sm">
                      <span className="text-slate-200 w-40 truncate">{p.product}</span>
                      <div className="flex-1 h-4 bg-[#111827] rounded-full overflow-hidden flex">
                        <div className="h-full bg-emerald-500" style={{ width: p.total ? `${((p.total - p.fake) / p.total) * 100}%` : '0%' }} />
                        <div className="h-full bg-red-500" style={{ width: p.total ? `${(p.fake / p.total) * 100}%` : '0%' }} />
                      </div>
                      <span className="text-slate-300/50 text-xs w-28 text-right">{p.total} reviews · {p.fake} fake</span>
                    </div>
                  ))}
                </div>
                <div className="flex gap-4 mt-3 text-xs text-slate-300/50">
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-emerald-500 inline-block"></span>Genuine</span>
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-red-500 inline-block"></span>Fake</span>
                </div>
              </div>
            )}

            <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4 text-sm text-blue-300">
              💡 CSV-uploaded reviews are automatically scored by the AI — confidence scores appear in All Reviews after upload completes.
            </div>
          </div>
        )}

        {/* ── CSV UPLOAD ── */}
        {tab === 'upload' && (
          <div className="space-y-6">
            <div className="bg-[#111827] border border-[#1e3a5f]/40 rounded-xl p-6">
              <h2 className="font-semibold mb-2">Upload Reviews CSV</h2>
              <p className="text-sm text-slate-400 mb-3">
                Supported columns: <code className="bg-[#111827] px-1 rounded">Comment</code> or <code className="bg-[#111827] px-1 rounded">text</code>, <code className="bg-[#111827] px-1 rounded">Rating</code>, <code className="bg-[#111827] px-1 rounded">Label</code> (0=genuine, 1=fake)
              </p>
              <div className="bg-[#111827]/50 rounded-lg p-4 mb-4 font-mono text-xs text-slate-200">
                <div className="text-slate-300/50 mb-1">Your CSV format:</div>
                <div>ProductID,UserID,Comment,Rating,Label</div>
                <div>1,1,"Great product!",5,0</div>
                <div>2,2,"Fake review!!",1,1</div>
              </div>
              <div className="flex gap-3 items-center flex-wrap">
                <input ref={fileRef} type="file" accept=".csv" onChange={e => setCsvFile(e.target.files[0])}
                  className="text-sm text-slate-200 file:bg-[#1e3a5f] file:border-0 file:text-slate-200 file:px-4 file:py-2 file:rounded-lg file:mr-3 file:cursor-pointer" />
                <button onClick={uploadCSV} disabled={!csvFile || uploading}
                  className="bg-[#3b82f6] hover:bg-[#3b82f6] disabled:opacity-50 text-white px-6 py-2 rounded-lg text-sm transition">
                  {uploading ? 'Processing...' : '📤 Upload CSV'}
                </button>
              </div>

              {/* Live progress bar */}
              {uploadProgress && (
                <div className="mt-4 space-y-2">
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span>
                      {uploadProgress.status === 'completed'
                        ? `✅ Done — ${uploadProgress.success} saved, ${uploadProgress.failed} failed`
                        : uploadProgress.status === 'failed'
                        ? '❌ Processing failed'
                        : `⚙️ Processing… ${uploadProgress.done} / ${uploadProgress.total} rows`}
                    </span>
                    <span className="font-mono">
                      {uploadProgress.total > 0
                        ? `${Math.round((uploadProgress.done / uploadProgress.total) * 100)}%`
                        : '—'}
                    </span>
                  </div>
                  <div className="h-2.5 w-full bg-[#111827] rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        uploadProgress.status === 'completed' ? 'bg-emerald-500'
                        : uploadProgress.status === 'failed' ? 'bg-red-500'
                        : 'bg-[#3b82f6] animate-pulse'
                      }`}
                      style={{ width: uploadProgress.total > 0
                        ? `${Math.round((uploadProgress.done / uploadProgress.total) * 100)}%`
                        : uploadProgress.status === 'processing' ? '5%' : '0%' }}
                    />
                  </div>
                  {uploadProgress.status === 'processing' && (
                    <p className="text-xs text-slate-300/50">
                      Rows are saved every 20 — you can switch tabs; this continues in the background.
                    </p>
                  )}
                </div>
              )}

              {uploadResult && (
                <div className={`mt-4 p-4 rounded-lg text-sm ${uploadResult.error ? 'bg-red-500/10 text-red-300 border border-red-500/20' : 'bg-emerald-500/10 text-slate-300 border border-emerald-500/20'}`}>
                  {uploadResult.error || `✅ ${uploadResult.detail}`}
                </div>
              )}
            </div>

            {/* Upload history */}
            <div className="bg-[#111827] border border-[#1e3a5f]/40 rounded-xl p-5">
              <h2 className="font-semibold mb-4">Upload History</h2>
              {batches.length === 0 ? <p className="text-slate-300/50 text-sm">No uploads yet.</p> : (
                <table className="w-full text-sm">
                  <thead><tr className="text-slate-300/50 border-b border-[#1e3a5f]/40 text-left">
                    <th className="py-2 pr-4">File</th><th className="py-2 pr-4">Total</th>
                    <th className="py-2 pr-4">Success</th><th className="py-2 pr-4">Failed</th>
                    <th className="py-2 pr-4">Status</th><th className="py-2">Uploaded</th>
                  </tr></thead>
                  <tbody>
                    {batches.map(b => (
                      <tr key={b.id} className="border-b border-[#1e3a5f]/20">
                        <td className="py-3 pr-4 text-slate-200">{b.filename}</td>
                        <td className="py-3 pr-4">{b.total_rows}</td>
                        <td className="py-3 pr-4 text-slate-400">{b.success_rows}</td>
                        <td className="py-3 pr-4 text-red-400">{b.failed_rows}</td>
                        <td className="py-3 pr-4">
                          <span className={`px-2 py-0.5 rounded text-xs ${b.status === 'completed' ? 'bg-emerald-500/20 text-slate-300' : 'bg-red-500/20 text-red-300'}`}>{b.status}</span>
                        </td>
                        <td className="py-3 text-slate-300/50 text-xs">{new Date(b.uploaded_at).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

        {/* ── ALL REVIEWS ── */}
        {tab === 'reviews' && (
          <div className="bg-[#111827] border border-[#1e3a5f]/40 rounded-xl p-5">
            <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
              <h2 className="font-semibold flex items-center gap-2">All Reviews {stats?.total ? `(${stats.total} total)` : ''} <span className="flex items-center gap-1 text-xs font-normal text-slate-400 bg-emerald-900/30 border border-emerald-500/30 px-2 py-0.5 rounded-full"><span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse inline-block"/>Live</span></h2>
              <div className="flex items-center gap-2 flex-wrap">
                {/* Filter buttons */}
                {['all', 'fake', 'genuine', 'pending'].map(f => (
                  <button key={f} onClick={() => { setReviewFilter(f); setReviewPage(1) }}
                    className={`px-3 py-1 rounded-lg text-xs transition ${reviewFilter === f
                      ? f === 'fake' ? 'bg-red-500/30 text-red-300' : f === 'genuine' ? 'bg-emerald-500/30 text-slate-300' : 'bg-[#3b82f6] text-white'
                      : 'bg-[#111827] text-slate-400 hover:text-slate-200'}`}>
                    {f === 'all' ? 'All' : f === 'fake' ? '🔴 Fake' : f === 'genuine' ? '🟢 Genuine' : '⏳ Pending'}
                  </button>
                ))}
                <button onClick={fetchReviews} className="text-xs text-slate-400 hover:text-slate-200 px-2">↻</button>
                <button onClick={backfillReasoning} className="text-xs text-slate-400 hover:text-slate-300 px-2 py-1 rounded border border-[#1e3a5f]/40 hover:border-violet-500/30 transition">⚡ Fix Explanations</button>

                {/* Clear all button */}
                {!confirmClear ? (
                  <button onClick={() => setConfirmClear(true)}
                    className="bg-red-500/20 hover:bg-red-500/30 text-red-300 text-xs px-4 py-1.5 rounded-lg transition border border-red-500/20">
                    🗑 Clear Dataset
                  </button>
                ) : (
                  <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-1.5">
                    <span className="text-red-300 text-xs">Delete all reviews?</span>
                    <button onClick={clearAllReviews} disabled={clearingAll}
                      className="text-xs bg-red-600 hover:bg-red-500 text-white px-3 py-1 rounded disabled:opacity-50">
                      {clearingAll ? 'Clearing...' : 'Yes, Delete'}
                    </button>
                    <button onClick={() => setConfirmClear(false)} className="text-xs text-slate-400 hover:text-slate-200">Cancel</button>
                  </div>
                )}
              </div>
            </div>

            {reviews.length === 0 ? (
              <p className="text-slate-300/50 text-sm py-8 text-center">No reviews found.</p>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead><tr className="text-slate-300/50 border-b border-[#1e3a5f]/40 text-left">
                      <th className="py-2 pr-4">ID</th>
                      <th className="py-2 pr-4">Text</th>
                      <th className="py-2 pr-4">Verdict</th>
                      <th className="py-2 pr-4">Confidence</th>
                      <th className="py-2 pr-4">Date</th>
                      <th className="py-2">Action</th>
                    </tr></thead>
                    <tbody>
                      {reviews.map(r => (
                        <React.Fragment key={r.id}>
                        <tr className="border-b border-[#1e3a5f]/20 hover:bg-[#1e3a5f]/20 group">
                          <td className="py-3 pr-4 text-slate-300/50 text-xs">#{r.id}</td>
                          <td className="py-3 pr-4 text-slate-200 max-w-sm">
                            <span className="truncate block max-w-xs" title={r.text || ''}>
                              {r.text || <span className="text-slate-300/40 italic">no text</span>}
                            </span>
                          </td>
                          <td className="py-3 pr-4">
                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                              r.verdict === 'fake' ? 'bg-red-500/20 text-red-300' :
                              r.verdict === 'genuine' ? 'bg-emerald-500/20 text-slate-300' :
                              'bg-[#1e3a5f] text-slate-400'}`}>
                              {r.verdict || 'pending'}
                            </span>
                          </td>
                          <td className="py-3 pr-4 text-slate-400 text-xs">
                            {r.confidence != null ? `${(r.confidence * 100).toFixed(1)}%` : <span className="text-slate-300/40">N/A</span>}
                          </td>
                          <td className="py-3 pr-4 text-slate-300/50 text-xs whitespace-nowrap">{new Date(r.created_at).toLocaleString()}</td>
                          <td className="py-3">
                            <div className="flex items-center gap-2">
                              {r.verdict === 'fake' && (
                                <button
                                  onClick={() => setExpandedReviewId(prev => prev === r.id ? null : r.id)}
                                  className="text-xs px-2 py-1 rounded bg-[#3b82f6]/20 text-slate-300 hover:bg-[#3b82f6]/30 transition"
                                >
                                  ✨ {expandedReviewId === r.id ? 'Hide' : 'Explain'}
                                </button>
                              )}
                              {r.verdict === 'fake' && (
                                <button
                                  onClick={() => handleDeleteReview(r.id)}
                                  disabled={deletingId === r.id}
                                  className="text-red-400 hover:text-red-200 text-xs disabled:opacity-40 px-2 py-1 rounded hover:bg-red-500/10 transition"
                                >
                                  {deletingId === r.id ? '...' : 'Delete'}
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                        {expandedReviewId === r.id && (
                          <tr className="border-b border-[#1e3a5f]/20 bg-rose-950/10">
                            <td colSpan={6} className="px-6 pb-3 pt-1">
                              <div className="rounded border border-rose-800/30 bg-rose-950/30 p-3 space-y-1">
                                {!r.reasoning ? (
                                  <div className="flex items-center gap-3 text-xs text-slate-400">
                                    <span className="italic">No reasoning stored for this review.</span>
                                    <button onClick={backfillReasoning} className="text-slate-300 hover:text-slate-200 underline whitespace-nowrap">⚡ Run Fix Explanations to generate</button>
                                  </div>
                                ) : getReasonPoints(r).length === 0 ? (
                                  <span className="text-xs text-slate-300/50 italic">No reasoning available. Click ⚡ Fix Explanations above.</span>
                                ) : getReasonPoints(r).map((p, i) => (
                                  <div key={i} className="flex gap-3 text-xs">
                                    <span className="text-slate-400 min-w-[180px] shrink-0">{p.label}</span>
                                    <span className="text-rose-200 font-medium">{p.value}</span>
                                  </div>
                                ))}
                              </div>
                            </td>
                          </tr>
                        )}
                        </React.Fragment>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Pagination */}
                <div className="flex items-center justify-between mt-4 text-sm">
                  <button onClick={() => setReviewPage(p => Math.max(1, p - 1))} disabled={reviewPage === 1}
                    className="px-4 py-1.5 bg-[#111827] rounded-lg disabled:opacity-40 hover:bg-[#1e3a5f] transition">
                    ← Prev
                  </button>
                  <span className="text-slate-300/50 text-xs">Page {reviewPage} · showing {reviews.length}</span>
                  <button onClick={() => setReviewPage(p => p + 1)} disabled={reviews.length < PAGE_SIZE}
                    className="px-4 py-1.5 bg-[#111827] rounded-lg disabled:opacity-40 hover:bg-[#1e3a5f] transition">
                    Next →
                  </button>
                </div>
              </>
            )}
          </div>
        )}

        {/* ── USERS ── */}
        {tab === 'users' && (
          <div className="bg-[#111827] border border-[#1e3a5f]/40 rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold">All Users ({users.length})</h2>
              <button onClick={fetchUsers} className="text-xs text-slate-400 hover:text-slate-200">↻ Refresh</button>
            </div>
            <table className="w-full text-sm">
              <thead><tr className="text-slate-300/50 border-b border-[#1e3a5f]/40 text-left">
                <th className="py-2 pr-4">Username</th><th className="py-2 pr-4">Role</th>
                <th className="py-2 pr-4">Status</th><th className="py-2 pr-4">Joined</th><th className="py-2">Actions</th>
              </tr></thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.id} className="border-b border-[#1e3a5f]/20 hover:bg-[#1e3a5f]/20">
                    <td className="py-3 pr-4 font-medium">{u.is_admin ? '👑 ' : u.role === 'Owner' ? '🏪 ' : '👤 '}{u.username}</td>
                    <td className="py-3 pr-4">
                      {u.is_admin ? (
                        <span className="text-xs text-yellow-300 bg-yellow-500/10 px-2 py-0.5 rounded">Admin</span>
                      ) : (
                        <select value={u.role} onChange={e => updateUserRole(u.id, e.target.value)}
                          className="bg-[#111827] border border-[#1e3a5f]/40 rounded px-2 py-1 text-xs text-slate-200">
                          <option value="User">User</option>
                          <option value="Owner">Owner</option>
                        </select>
                      )}
                    </td>
                    <td className="py-3 pr-4">
                      <span className={`text-xs px-2 py-0.5 rounded ${u.is_active ? 'bg-emerald-500/20 text-slate-300' : 'bg-[#1e3a5f] text-slate-300/50'}`}>
                        {u.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="py-3 pr-4 text-slate-300/50 text-xs">{new Date(u.created_at).toLocaleDateString()}</td>
                    <td className="py-3">
                      {!u.is_admin && (
                        <button onClick={() => toggleUserActive(u.id, u.is_active)}
                          className={`text-xs px-3 py-1.5 rounded-lg transition ${u.is_active ? 'bg-red-500/20 text-red-300 hover:bg-red-500/30' : 'bg-emerald-500/20 text-slate-300 hover:bg-emerald-500/30'}`}>
                          {u.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* ── AUDIT LOG ── */}
        {tab === 'audit' && (() => {
          const actionIcon = (a) => {
            if (a.includes('delete'))   return { icon: '🗑', cls: 'bg-red-500/20 text-red-300' }
            if (a.includes('cancel'))   return { icon: '✖', cls: 'bg-red-500/20 text-red-300' }
            if (a.includes('flag'))     return { icon: '🚩', cls: 'bg-yellow-500/20 text-yellow-300' }
            if (a.includes('unflag'))   return { icon: '✅', cls: 'bg-green-500/20 text-green-300' }
            if (a.includes('ship'))     return { icon: '📦', cls: 'bg-purple-500/20 text-purple-300' }
            if (a.includes('deliver'))  return { icon: '✅', cls: 'bg-green-500/20 text-green-300' }
            if (a.includes('order'))    return { icon: '🛒', cls: 'bg-blue-500/20 text-blue-300' }
            return { icon: '📋', cls: 'bg-[#3b82f6]/20 text-slate-300' }
          }
          const fmtAction = (a) => a.replace(/_/g, ' ')
          const fmtDetails = (d) => {
            try { const p = JSON.parse(d); return Object.entries(p).map(([k,v]) => `${k}: ${v}`).join(' · ') }
            catch { return d }
          }
          return (
            <div className="bg-[#111827] border border-[#1e3a5f]/40 rounded-xl p-5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold">Audit Log <span className="text-slate-300/50 text-sm font-normal">({auditLogs.length} events)</span></h2>
                <button onClick={fetchAuditLogs} className="text-xs text-slate-400 hover:text-slate-200">↻ Refresh</button>
              </div>
              {auditLogs.length === 0 ? <p className="text-slate-300/50 text-sm">No events yet.</p> : (
                <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
                  {auditLogs.map(log => {
                    const { icon, cls } = actionIcon(log.action || '')
                    return (
                      <div key={log.id} className="flex items-start gap-3 bg-[#111827]/30 rounded-lg p-3">
                        <span className="text-slate-300/50 text-xs whitespace-nowrap w-36 shrink-0 mt-0.5">
                          {new Date(log.created_at).toLocaleString()}
                        </span>
                        <span className={`text-xs px-2 py-0.5 rounded whitespace-nowrap shrink-0 ${cls}`}>
                          {icon} {fmtAction(log.action)}
                        </span>
                        <div className="flex flex-col gap-0.5 min-w-0">
                          <span className="text-slate-200 text-xs font-semibold">
                            by {log.actor_username || (log.actor_user_id ? `user #${log.actor_user_id}` : 'system')}
                            {log.target_review_id && <span className="text-slate-300/50 font-normal ml-2">review #{log.target_review_id}</span>}
                            {log.target_order_id  && <span className="text-slate-300/50 font-normal ml-2">order #{String(log.target_order_id).padStart(6,'0')}</span>}
                          </span>
                          {log.details && (
                            <span className="text-slate-300/50 text-xs truncate">{fmtDetails(log.details)}</span>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )
        })()}
      </div>
    </div>
  )
}






