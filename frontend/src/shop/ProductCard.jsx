import React from 'react'
import { API_BASE, catIcon } from './shopApi'

export default function ProductCard({ p, onAddCart, onViewReviews }) {
  const fakeRatio = p.review_count > 0 ? (p.fake_count / p.review_count) : 0
  const genuineRatio = p.review_count > 0 ? (p.genuine_count / p.review_count) : 0
  const trustScore = Math.round(genuineRatio * 100)
  
  const getTrustBadge = () => {
    if (p.review_count === 0) {
      return {
        icon: '🔹',
        label: 'No Reviews',
        bg: 'bg-slate-100',
        text: 'text-slate-500',
        border: 'border-slate-200'
      }
    }
    
    if (fakeRatio < 0.1) {
      return {
        icon: '✓',
        label: `${trustScore}% Verified`,
        bg: 'bg-emerald-50',
        text: 'text-emerald-700',
        border: 'border-emerald-200'
      }
    } else if (fakeRatio < 0.3) {
      return {
        icon: '⚡',
        label: `${trustScore}% Trust`,
        bg: 'bg-amber-50',
        text: 'text-amber-700',
        border: 'border-amber-200'
      }
    } else {
      return {
        icon: '⚠',
        label: 'Low Trust',
        bg: 'bg-red-50',
        text: 'text-red-700',
        border: 'border-red-200'
      }
    }
  }
  
  const badge = getTrustBadge()

  return (
    <div className="bg-white border-2 border-slate-200 rounded-2xl overflow-hidden hover:-translate-y-1 hover:shadow-xl hover:border-blue-300 transition-all duration-200 cursor-pointer group">
      <div className="h-36 bg-slate-100 flex items-center justify-center border-b border-slate-200 overflow-hidden relative">
        {p.image_filename
          ? <img src={`${API_BASE}/static/uploads/${p.image_filename}`} alt={p.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              onError={e => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex' }} />
          : null}
        <div className={`text-5xl w-full h-full items-center justify-center ${p.image_filename ? 'hidden' : 'flex'}`}>
          {catIcon(p.category)}
        </div>
        
        {/* Trust Badge Overlay */}
        <div className="absolute top-2 right-2">
          <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-[10px] font-bold ${badge.bg} ${badge.text} border ${badge.border} shadow-sm backdrop-blur-sm`}>
            <span>{badge.icon}</span>
            <span>{badge.label}</span>
          </div>
        </div>
      </div>
      
      <div className="p-4">
        <div className="text-[10px] font-bold uppercase tracking-widest text-blue-600 mb-1">{p.category}</div>
        <div className="font-bold text-slate-800 text-sm leading-tight mb-1 line-clamp-2">{p.name}</div>
        <div className="text-xl font-black text-[#0a1628] mb-2">₹{p.price?.toLocaleString()}</div>
        
        {/* Rating and Review Stats */}
        <div className="flex items-center gap-2 mb-3">
          <span className="text-yellow-500 text-sm font-bold">
            {'★'.repeat(Math.round(p.avg_rating || 0))}{'☆'.repeat(5 - Math.round(p.avg_rating || 0))}
          </span>
          <span className="text-xs text-slate-400">({p.review_count || 0})</span>
        </div>
        
        {/* AI Verification Stats */}
        {p.review_count > 0 && (
          <div className="flex items-center gap-2 mb-3 text-[10px]">
            <div className="flex items-center gap-1 text-green-600">
              <span>✓</span>
              <span className="font-semibold">{p.genuine_count || 0}</span>
            </div>
            {p.fake_count > 0 && (
              <>
                <span className="text-slate-300">•</span>
                <div className="flex items-center gap-1 text-red-600">
                  <span>⚠</span>
                  <span className="font-semibold">{p.fake_count || 0} flagged</span>
                </div>
              </>
            )}
            <span className="ml-auto text-slate-400">🛡️ AI checked</span>
          </div>
        )}
        
        <div className="flex gap-2">
          <button onClick={() => onAddCart(p.id)} className="flex-1 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white text-xs font-bold rounded-lg transition shadow-sm">
            Add to Cart
          </button>
          <button onClick={() => onViewReviews(p)} className="px-3 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-lg transition border border-slate-200">
            Reviews
          </button>
        </div>
      </div>
    </div>
  )
}
