import React from 'react'

export default function ROCChart({curves}){
  const metrics = curves || {
    late_fusion_auc: 0.86,
    attention_fusion_auc: 0.91,
    text_auc: 0.82,
    metadata_auc: 0.84,
  }

  const models = [
    { key: 'attention_fusion_auc', label: 'Attention Fusion', color: '#22c55e' },
    { key: 'late_fusion_auc',      label: 'Late Fusion',      color: '#6366f1' },
    { key: 'metadata_auc',         label: 'Metadata',         color: '#f59e0b' },
    { key: 'text_auc',             label: 'Text',             color: '#f43f5e' },
  ]

  const maxAUC = 1.0
  const minAUC = 0.7

  return (
    <div className="rounded border border-white/10 bg-[#111827] p-4">
      <div className="font-semibold text-slate-100 mb-1">Model AUC Comparison</div>
      <div className="text-xs text-slate-400 mb-4">Higher is better — max score is 1.0</div>

      <div className="space-y-3">
        {models.map((m, i) => {
          const val = Number(metrics[m.key])
          const pct = ((val - minAUC) / (maxAUC - minAUC)) * 100
          return (
            <div key={m.key}>
              <div className="flex justify-between items-center mb-1">
                <span style={{color: m.color, fontSize: 13, fontWeight: 600}}>{m.label}</span>
                <span style={{color: m.color, fontSize: 13, fontWeight: 700}}>{val.toFixed(2)}</span>
              </div>
              <div style={{background:'#1f2937', borderRadius:6, height:18, overflow:'hidden'}}>
                <div style={{
                  width: `${pct}%`,
                  height: '100%',
                  background: `linear-gradient(90deg, ${m.color}99, ${m.color})`,
                  borderRadius: 6,
                  transition: 'width 0.6s ease',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'flex-end',
                  paddingRight: 6,
                }}>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Scale labels */}
      <div className="flex justify-between mt-3 text-xs text-[#334155]">
        <span>0.70</span>
        <span>0.78</span>
        <span>0.85</span>
        <span>0.93</span>
        <span>1.00</span>
      </div>
      <div className="mt-3 text-xs text-[#334155] text-center">
        AUC Score (Area Under ROC Curve)
      </div>
    </div>
  )
}
