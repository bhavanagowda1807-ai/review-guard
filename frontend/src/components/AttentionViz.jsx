import React from 'react'

const LABELS = { text: 'Text', meta: 'Metadata' }
const COLORS = { text: 'bg-indigo-400', meta: 'bg-emerald-400' }

export default function AttentionViz({ attention }) {
  // attention: { text: 0.65, meta: 0.35 }  (image removed)
  const items = Object.entries(attention || {}).filter(([k]) => k !== 'image')

  return (
    <div className="rounded border border-[#334155] bg-[#111827] p-4">
      <div className="mb-3 font-semibold">Modality Attention</div>
      {!items.length && (
        <div className="text-sm text-slate-400">Attention weights appear after inference.</div>
      )}
      {items.map(([k, v]) => (
        <div key={k} className="mb-3">
          <div className="flex justify-between text-sm text-slate-300">
            <span>{LABELS[k] || k}</span>
            <span>{(v * 100).toFixed(0)}%</span>
          </div>
          <div className="mt-1 h-2 rounded bg-[#1f2937]">
            <div style={{ width: `${v * 100}%` }} className={`h-2 rounded ${COLORS[k] || 'bg-indigo-400'}`} />
          </div>
        </div>
      ))}
    </div>
  )
}
