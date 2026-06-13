import React, { useEffect, useState } from 'react'
import { apiFetch, CATEGORIES } from './shopApi'
import ProductCard from './ProductCard'

export default function ProductsPage({ user, setPage, onAddCart, onViewReviews }) {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [category, setCategory] = useState('All')
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState('default')

  useEffect(() => { load() }, [])

  async function load() {
    setLoading(true)
    try { setProducts(await apiFetch('/api/shop/products')) } catch { setProducts([]) }
    setLoading(false)
  }

  const filtered = products
    .filter(p => category === 'All' || p.category === category)
    .filter(p => !search || p.name?.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => {
      if (sort === 'price-asc')  return a.price - b.price
      if (sort === 'price-desc') return b.price - a.price
      if (sort === 'rating')     return (b.avg_rating || 0) - (a.avg_rating || 0)
      if (sort === 'reviews')    return (b.review_count || 0) - (a.review_count || 0)
      return 0
    })

  return (
    <div>
      <div className="bg-white border-b border-slate-200 px-5 py-3 flex flex-wrap gap-3 items-center">
        <div className="flex gap-1.5 flex-wrap">
          {CATEGORIES.map(c => (
            <button key={c} onClick={() => setCategory(c)}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold transition ${category === c ? 'bg-[#0a1628] text-white' : 'border border-slate-200 text-slate-600 hover:border-slate-400'}`}>
              {c}
            </button>
          ))}
        </div>
        <div className="flex gap-2 ml-auto">
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search products…"
            className="px-3 py-1.5 text-sm border border-slate-200 rounded-lg text-slate-700 outline-none focus:border-sky-400 w-44" />
          <select value={sort} onChange={e => setSort(e.target.value)}
            className="px-3 py-1.5 text-sm border border-slate-200 rounded-lg text-slate-700 outline-none">
            <option value="default">Sort: Default</option>
            <option value="price-asc">Price: Low→High</option>
            <option value="price-desc">Price: High→Low</option>
            <option value="rating">Top Rated</option>
            <option value="reviews">Most Reviews</option>
          </select>
        </div>
      </div>
      <div className="p-5">
        <div className="text-sm text-slate-500 mb-4">{filtered.length} products</div>
        {loading
          ? <div className="text-slate-400 text-center py-20">Loading…</div>
          : filtered.length === 0
            ? <div className="text-slate-400 text-center py-20">No products found</div>
            : <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
                {filtered.map(p => <ProductCard key={p.id} p={p} onAddCart={onAddCart} onViewReviews={onViewReviews} />)}
              </div>
        }
      </div>
    </div>
  )
}
