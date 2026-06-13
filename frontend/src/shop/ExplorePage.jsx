import React, { useEffect, useState } from 'react'
import { apiFetch, CATEGORIES } from './shopApi'
import ProductCard from './ProductCard'

export default function ExplorePage({ onAddCart, onViewReviews }) {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [category, setCategory] = useState('All')

  useEffect(() => { load() }, [])

  async function load() {
    setLoading(true)
    try { setProducts(await apiFetch('/api/shop/rankings')) } catch { setProducts([]) }
    setLoading(false)
  }

  const filtered = products.filter(p => category === 'All' || p.category === category)

  return (
    <div className="p-5">
      <h2 className="text-xl font-bold text-slate-800 mb-1">Content-Based Explore</h2>
      <p className="text-sm text-slate-500 mb-4">Products ranked by verified positive review ratios — fake reviews excluded from scoring.</p>
      <div className="bg-sky-50 border border-sky-200 rounded-xl px-4 py-3 mb-4 text-sm text-sky-700">
        <strong>Smart sort active:</strong> Products ranked by verified positive review ratio. Fake reviews excluded from scoring.
      </div>
      <div className="flex flex-wrap gap-2 mb-5">
        {CATEGORIES.map(c => (
          <button key={c} onClick={() => setCategory(c)}
            className={`px-3 py-1.5 rounded-full text-xs font-semibold transition ${category === c ? 'bg-[#0a1628] text-white' : 'border border-slate-200 text-slate-600 hover:border-slate-400'}`}>
            {c}
          </button>
        ))}
      </div>
      {loading
        ? <div className="text-slate-400 text-center py-20">Loading…</div>
        : <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {filtered.map(p => <ProductCard key={p.id} p={p} onAddCart={onAddCart} onViewReviews={onViewReviews} />)}
          </div>
      }
    </div>
  )
}
