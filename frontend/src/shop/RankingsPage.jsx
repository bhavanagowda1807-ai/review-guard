import React, { useEffect, useState } from 'react'
import { apiFetch, catIcon } from './shopApi'

export default function RankingsPage() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [category, setCategory] = useState('All')

  useEffect(() => { load() }, [])

  async function load() {
    setLoading(true)
    try { setData(await apiFetch('/api/shop/rankings')) } catch { setData([]) }
    setLoading(false)
  }

  const filtered = data.filter(p => category === 'All' || p.category === category)

  return (
    <div className="p-5 max-w-3xl mx-auto">
      <h2 className="text-xl font-bold text-slate-800 mb-1">Product Rankings</h2>
      <p className="text-sm text-slate-500 mb-4">
        Rankings computed using verified positive review ratios after AI-based fake review removal.
      </p>
      <div className="flex flex-wrap gap-2 mb-5">
        {['All', 'Electronics', 'Clothing', 'Books', 'Beauty'].map(c => (
          <button key={c} onClick={() => setCategory(c)}
            className={`px-3 py-1.5 rounded-full text-xs font-semibold transition ${category === c ? 'bg-[#0a1628] text-white' : 'border border-slate-200 text-slate-600 hover:border-slate-400'}`}>
            {c}
          </button>
        ))}
      </div>
      {loading
        ? <div className="text-slate-400 text-center py-20">Loading…</div>
        : <div className="space-y-3">
            {filtered.map((p, i) => {
              const trustScore = p.review_count > 0
                ? Math.round(((p.genuine_count || 0) / p.review_count) * 100)
                : 0
              return (
                <div key={p.id} className="bg-white border border-slate-200 rounded-xl p-4 flex items-center gap-4 shadow-sm">
                  <div className="text-2xl font-black text-slate-300 w-8 text-center">#{i + 1}</div>
                  <div className="text-3xl">{catIcon(p.category)}</div>
                  <div className="flex-1 min-w-0">
                    <div className="font-bold text-slate-800 text-sm truncate">{p.name}</div>
                    <div className="text-xs text-slate-400">{p.category} · {p.review_count} reviews</div>
                    <div className="mt-1.5 h-2 bg-slate-100 rounded-full overflow-hidden w-48">
                      <div className="h-full bg-green-400 rounded-full" style={{ width: `${trustScore}%` }} />
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-black text-slate-800 text-lg">₹{p.price?.toLocaleString()}</div>
                    <div className="text-xs text-green-500 font-bold">{trustScore}% trusted</div>
                  </div>
                </div>
              )
            })}
          </div>
      }
    </div>
  )
}
