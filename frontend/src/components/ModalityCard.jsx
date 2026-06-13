import React from 'react'

export default function ModalityCard({title, score, details, features}){
  const pct = typeof score === 'number' ? `${(score*100).toFixed(1)}%` : 'Missing'
  return (
    <div className="rounded border border-[#334155] bg-[#111827] p-4">
      <div className="flex items-center justify-between gap-3">
        <div className="font-semibold">{title}</div>
        <div className="rounded bg-white/10 px-2 py-1 text-xs text-slate-300">{pct}</div>
      </div>
      {details && <div className="mt-3 text-sm text-slate-300">{typeof details === 'string' ? details : 'Feature contribution available'}</div>}
      {features && <div className="mt-3 max-h-28 overflow-auto rounded bg-[#1f2937] p-2 text-xs text-slate-400">
        {Object.entries(features).slice(0, 8).map(([key,value]) => (
          <div key={key} className="flex justify-between gap-3"><span>{key}</span><span>{typeof value === 'number' ? value.toFixed(3) : String(value).slice(0, 18)}</span></div>
        ))}
      </div>}
    </div>
  )
}
