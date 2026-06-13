import React from 'react'
import ProductCard from './ProductCard'

export default function HomePage({ setPage, user, products, onAddCart, onViewReviews }) {
  const featured = products.slice(0, 4)
  const topRated = [...products].sort((a, b) => (b.avg_rating || 0) - (a.avg_rating || 0)).slice(0, 4)

  // Calculate live stats
  const totalReviews = products.reduce((sum, p) => sum + (p.review_count || 0), 0)
  const totalVerified = products.reduce((sum, p) => sum + (p.genuine_count || 0), 0)
  const totalFlagged = products.reduce((sum, p) => sum + (p.fake_count || 0), 0)

  return (
    <div className="p-5 max-w-6xl mx-auto">
      {/* Hero */}
      <div className="bg-gradient-to-br from-[#0a1628] via-[#1e3f70] to-[#0a1628] rounded-2xl p-8 mb-8 relative overflow-hidden shadow-2xl">
        {/* Animated background elements */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl"></div>
        
        <div className="relative z-10">
          <div className="inline-flex items-center gap-2 text-xs font-bold text-sky-300 bg-sky-400/15 px-3 py-1.5 rounded-full mb-4 tracking-widest uppercase border border-sky-400/30">
            <span className="w-1.5 h-1.5 rounded-full bg-sky-400 inline-block animate-pulse" />
            ReviewGuard AI Protection
          </div>
          <h1 className="text-4xl font-black text-white mb-3 leading-tight">
            Shop with confidence.<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-300 to-blue-400">Every review AI-verified.</span>
          </h1>
          <p className="text-white/70 text-sm max-w-2xl mb-6 leading-relaxed">
            Our multimodal ML system analyzes every review using text analysis, behavioral patterns, and metadata detection — 
            ensuring you always see authentic, trustworthy feedback.
          </p>
          
          {/* Live Stats */}
          <div className="grid grid-cols-3 gap-4 mb-6 max-w-xl">
            <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl p-3">
              <div className="text-2xl font-black text-white">{totalReviews}</div>
              <div className="text-[10px] text-white/60 uppercase tracking-wide font-semibold">Reviews Analyzed</div>
            </div>
            <div className="bg-emerald-500/20 backdrop-blur-sm border border-emerald-400/30 rounded-xl p-3">
              <div className="text-2xl font-black text-emerald-300">{totalVerified}</div>
              <div className="text-[10px] text-emerald-200/80 uppercase tracking-wide font-semibold">Verified Genuine</div>
            </div>
            <div className="bg-red-500/20 backdrop-blur-sm border border-red-400/30 rounded-xl p-3">
              <div className="text-2xl font-black text-red-300">{totalFlagged}</div>
              <div className="text-[10px] text-red-200/80 uppercase tracking-wide font-semibold">Fake Detected</div>
            </div>
          </div>
          
          <div className="flex gap-3 flex-wrap">
            <button onClick={() => setPage('products')} className="px-6 py-3 bg-gradient-to-r from-sky-400 to-blue-500 hover:from-sky-500 hover:to-blue-600 text-white font-bold text-sm rounded-xl transition shadow-lg shadow-blue-500/30">
              Browse All Products
            </button>
            <button onClick={() => setPage('rankings')} className="px-6 py-3 border-2 border-white/30 hover:bg-white/10 text-white font-semibold text-sm rounded-xl transition backdrop-blur-sm">
              View Trust Rankings
            </button>
          </div>
        </div>
      </div>

      {/* Trust Guarantee Banner */}
      <div className="bg-gradient-to-r from-emerald-50 to-green-50 border-2 border-emerald-200 rounded-xl p-4 mb-8 flex items-center gap-4">
        <div className="w-12 h-12 bg-emerald-500 rounded-full flex items-center justify-center flex-shrink-0">
          <span className="text-2xl">🛡️</span>
        </div>
        <div className="flex-1">
          <div className="font-bold text-emerald-900 mb-0.5">100% AI-Protected Shopping</div>
          <div className="text-sm text-emerald-700">Every product review is automatically analyzed by ReviewGuard's multimodal detection system</div>
        </div>
        <button 
          onClick={() => window.location.href = '/reviewguard'}
          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg transition whitespace-nowrap"
        >
          See How It Works
        </button>
      </div>

      {/* Featured */}
      {featured.length > 0 && (
        <>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-bold text-slate-800">Featured Products</h2>
              <p className="text-xs text-slate-500 mt-0.5">Handpicked selection with verified reviews</p>
            </div>
            <button onClick={() => setPage('products')} className="text-sm text-blue-600 font-semibold hover:text-blue-700 flex items-center gap-1">
              View all <span>→</span>
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
            {featured.map(p => <ProductCard key={p.id} p={p} onAddCart={onAddCart} onViewReviews={onViewReviews} />)}
          </div>
        </>
      )}

      {/* Top Rated */}
      {topRated.length > 0 && (
        <>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-bold text-slate-800">Top Rated This Week</h2>
              <p className="text-xs text-slate-500 mt-0.5">Highest rated products based on genuine reviews only</p>
            </div>
            <button onClick={() => setPage('rankings')} className="text-sm text-blue-600 font-semibold hover:text-blue-700 flex items-center gap-1">
              Full rankings <span>→</span>
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {topRated.map(p => <ProductCard key={p.id} p={p} onAddCart={onAddCart} onViewReviews={onViewReviews} />)}
          </div>
        </>
      )}
      
      {/* Footer */}
      <div className="mt-12 pt-8 border-t border-slate-200 text-center">
        <div className="text-xs text-slate-400 mb-2">
          This is a demo environment showcasing ReviewGuard's AI detection capabilities
        </div>
        <div className="flex items-center justify-center gap-2 text-xs text-slate-500">
          <span>🔒</span>
          <span>Powered by</span>
          <span className="font-bold text-blue-600">ReviewGuard</span>
          <span>•</span>
          <span>Multimodal AI • LIME • SHAP • Attention Fusion</span>
        </div>
      </div>
    </div>
  )
}
