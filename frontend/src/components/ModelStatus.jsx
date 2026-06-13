import React, {useEffect, useState} from 'react'
import {Activity, DatabaseZap} from 'lucide-react'
import {getHealth, getModelCard} from '../services/api'

export default function ModelStatus(){
  const [health, setHealth] = useState(null)
  const [card, setCard] = useState(null)

  useEffect(() => {
    let alive = true
    Promise.allSettled([getHealth(), getModelCard()]).then(([healthResult, cardResult]) => {
      if (!alive) return
      if (healthResult.status === 'fulfilled') setHealth(healthResult.value)
      if (cardResult.status === 'fulfilled') setCard(cardResult.value)
    })
    return () => { alive = false }
  }, [])

  const models = health?.models || {}

  return (
    <div className="rounded border border-[#334155] bg-[#111827] p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2 font-semibold"><Activity size={16}/> Model Runtime</div>
        <div className={health?.status === 'ok' ? 'text-xs text-emerald-300' : 'text-xs text-slate-200'}>{health?.status || 'unknown'}</div>
      </div>
      <div className="grid grid-cols-2 gap-2 text-xs text-slate-300 md:grid-cols-4">
        {Object.entries(models).map(([name, value]) => (
          <div key={name} className="rounded bg-[#1f2937] p-2">
            <div className="capitalize text-slate-200">{name}</div>
            <div className="mt-1 text-slate-400">{value.deep_loaded ? 'deep on' : 'fallback'}</div>
            <div className="text-slate-400">{value.classifier_loaded ? 'artifact loaded' : 'no artifact'}</div>
          </div>
        ))}
      </div>
      {card && (
        <div className="mt-3 rounded bg-[#1f2937] p-3 text-xs text-slate-300">
          <div className="mb-2 flex items-center gap-2 text-slate-200"><DatabaseZap size={14}/> Capabilities</div>
          <div>Modalities: {(card.modalities || []).join(', ')}</div>
          <div>Fusion: {(card.fusion || []).join(', ')}</div>
        </div>
      )}
    </div>
  )
}
