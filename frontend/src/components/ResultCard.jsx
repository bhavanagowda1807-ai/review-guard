import React from 'react'

export default function ResultCard({verdict, confidence, genuineProbability, strategy}){
  const isFake = verdict === 'fake'
  return (
    <div className={`rounded border p-5 ${isFake ? 'border-rose-500/30 bg-rose-500/10' : 'border-emerald-500/30 bg-emerald-500/10'}`}>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="text-sm uppercase tracking-wide text-slate-400">Verdict</div>
          <div className={`mt-1 text-3xl font-semibold ${isFake ? 'text-rose-300' : 'text-emerald-300'}`}>{verdict?.toUpperCase()}</div>
        </div>
        <div className="text-right">
          <div className="text-sm text-slate-400">Confidence</div>
          <div className="text-2xl font-semibold">{((confidence || 0)*100).toFixed(1)}%</div>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3 text-sm text-slate-300">
        <div className="rounded bg-[#1f2937] p-3">Genuine probability: {((genuineProbability || 0)*100).toFixed(1)}%</div>
        <div className="rounded bg-[#1f2937] p-3">Fusion strategy: {strategy || 'attention'}</div>
      </div>
    </div>
  )
}
