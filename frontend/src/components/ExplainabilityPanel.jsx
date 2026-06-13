import React from 'react'

export default function ExplainabilityPanel({ explainability }) {
  if (!explainability) return null

  return (
    <div className="space-y-4 rounded border border-[#334155] bg-[#111827] p-4">
      <div className="font-semibold">Explainability Analysis</div>

      {explainability.lime && (
        <div className="rounded bg-[#1f2937] p-3 text-sm">
          <div className="font-medium mb-2">Text — LIME feature weights</div>
          <div className="grid gap-1 text-xs text-slate-300">
            {Object.entries(explainability.lime.feature_weights || {}).map(([word, weight]) => (
              <div key={word} className="flex items-center gap-2">
                <span className="w-28 truncate">{word}</span>
                <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${weight >= 0 ? 'bg-emerald-400' : 'bg-red-400'}`}
                    style={{ width: `${Math.min(Math.abs(weight) * 100, 100)}%` }}
                  />
                </div>
                <span className="w-12 text-right">{(weight * 100).toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {explainability.shap && (
        <div className="rounded bg-[#1f2937] p-3 text-sm">
          <div className="font-medium mb-2">Metadata — SHAP values</div>
          {explainability.shap.error ? (
            <div className="text-xs text-red-300">{explainability.shap.error}</div>
          ) : (
            <div className="grid gap-1 text-xs text-slate-300">
              {(explainability.shap.shap?.feature_names || explainability.shap.feature_names || []).map((name, i) => {
                const val = explainability.shap.shap?.shap_values?.[i] ?? explainability.shap.shap_values?.[i] ?? 0
                return (
                  <div key={name} className="flex items-center gap-2">
                    <span className="w-36 truncate">{name}</span>
                    <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${val >= 0 ? 'bg-emerald-400' : 'bg-red-400'}`}
                        style={{ width: `${Math.min(Math.abs(val) * 200, 100)}%` }}
                      />
                    </div>
                    <span className="w-14 text-right">{Number(val).toFixed(3)}</span>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {explainability.attention && (
        <div className="rounded bg-[#1f2937] p-3 text-sm">
          <div className="font-medium mb-2">Fusion — Attention weights</div>
          <div className="text-xs text-slate-300 space-y-1">
            {explainability.attention.interpretation &&
              Object.values(explainability.attention.interpretation).map((msg, i) => (
                <div key={i}>{msg}</div>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}
