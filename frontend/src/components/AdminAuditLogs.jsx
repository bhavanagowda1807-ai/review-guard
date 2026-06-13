import React, { useEffect, useState } from 'react'
import { listAuditLogs } from '../services/api'

const ACTION_CFG = (a = '') => {
  if (a.includes('delete'))  return { icon: '🗑', cls: 'bg-red-500/20 text-red-300' }
  if (a.includes('cancel'))  return { icon: '✖', cls: 'bg-red-500/20 text-red-300' }
  if (a.includes('unflag'))  return { icon: '✅', cls: 'bg-green-500/20 text-green-300' }
  if (a.includes('flag'))    return { icon: '🚩', cls: 'bg-yellow-500/20 text-yellow-300' }
  if (a.includes('ship'))    return { icon: '📦', cls: 'bg-purple-500/20 text-purple-300' }
  if (a.includes('deliver')) return { icon: '✅', cls: 'bg-green-500/20 text-green-300' }
  if (a.includes('order'))   return { icon: '🛒', cls: 'bg-blue-500/20 text-blue-300' }
  return { icon: '📋', cls: 'bg-indigo-500/20 text-slate-300' }
}

function fmtDetails(d) {
  try { return Object.entries(JSON.parse(d)).map(([k, v]) => `${k}: ${v}`).join(' · ') }
  catch { return d }
}

export default function AdminAuditLogs() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(50)
  const [total, setTotal] = useState(0)

  const load = async (p = 1) => {
    setLoading(true)
    setError(null)
    try {
      const data = await listAuditLogs(p, pageSize)
      setLogs(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
      console.error('Failed to load audit logs', err)
      setError(err?.response?.data?.detail || err?.message || 'Failed to load audit logs')
      setLogs([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load(page) }, [page])

  const hasMore = total > page * pageSize

  return (
    <div className="rounded border border-[#334155] bg-[#111827] p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="font-semibold">Audit Log <span className="text-slate-200 text-xs font-normal">({total} events)</span></div>
        <button onClick={() => load(page)} className="text-xs text-slate-400 hover:text-slate-200">↻ Refresh</button>
      </div>

      {loading && <div className="text-sm text-slate-400 py-4 text-center">Loading...</div>}

      {error && (
        <div className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded p-3 mb-3">
          ⚠ {error}
        </div>
      )}

      {!loading && !error && logs.length === 0 && (
        <div className="text-sm text-slate-200 py-4 text-center">No audit entries yet.</div>
      )}

      <div className="space-y-2 text-xs text-slate-400">
        {logs.map(log => {
          const { icon, cls } = ACTION_CFG(log.action)
          return (
            <div key={log.id} className="rounded bg-[#1f2937] p-2">
              <div className="flex items-start gap-2 flex-wrap">
                <span className="font-mono text-xs text-slate-200 whitespace-nowrap">
                  {new Date(log.created_at).toLocaleString()}
                </span>
                <span className={`text-xs px-2 py-0.5 rounded whitespace-nowrap ${cls}`}>
                  {icon} {log.action?.replace(/_/g, ' ')}
                </span>
                <span className="text-slate-300 text-xs">
                  by <strong>{log.actor_username || (log.actor_user_id ? `user #${log.actor_user_id}` : 'system')}</strong>
                  {log.target_review_id && <span className="text-slate-200 ml-2">review #{log.target_review_id}</span>}
                  {log.target_order_id  && <span className="text-slate-200 ml-2">order #{String(log.target_order_id).padStart(6,'0')}</span>}
                </span>
              </div>
              {log.details && (
                <div className="mt-1 text-xs text-slate-200 pl-1">{fmtDetails(log.details)}</div>
              )}
            </div>
          )
        })}
      </div>

      <div className="mt-3 flex items-center gap-2">
        <button disabled={page <= 1} onClick={() => setPage(p => Math.max(1, p - 1))}
          className="rounded bg-white/5 px-2 py-1 text-xs disabled:opacity-40">Prev</button>
        <div className="text-xs text-slate-400">Page {page}</div>
        <button disabled={!hasMore} onClick={() => setPage(p => p + 1)}
          className="rounded bg-white/5 px-2 py-1 text-xs disabled:opacity-40">Next</button>
        <div className="ml-auto text-xs text-slate-400">{total} total</div>
      </div>
    </div>
  )
}
