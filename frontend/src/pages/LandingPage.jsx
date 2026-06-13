import React, { useEffect, useState } from 'react'

export default function LandingPage({ navigate }) {
  const [visible, setVisible] = useState(false)
  const [hovered, setHovered] = useState(null)

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 60)
    return () => clearTimeout(t)
  }, [])

  return (
    <div className="min-h-screen bg-[#07090f] flex flex-col items-center justify-center p-6 overflow-hidden relative">

      {/* Background grid */}
      <div className="pointer-events-none absolute inset-0" style={{
        backgroundImage: 'linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)',
        backgroundSize: '48px 48px',
      }} />

      {/* Ambient glows */}
      <div className="pointer-events-none absolute -top-40 -left-40 w-[500px] h-[500px] rounded-full"
        style={{ background: 'radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%)' }} />
      <div className="pointer-events-none absolute -bottom-40 -right-40 w-[500px] h-[500px] rounded-full"
        style={{ background: 'radial-gradient(circle, rgba(14,165,233,0.12) 0%, transparent 70%)' }} />

      {/* Header */}
      <div
        className="text-center mb-14 transition-all duration-700"
        style={{ opacity: visible ? 1 : 0, transform: visible ? 'translateY(0)' : 'translateY(-20px)' }}
      >
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-white/10 bg-white/5 text-xs text-slate-400 tracking-widest uppercase mb-6">
          <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block animate-pulse" />
          Multimodal AI-Powered Review Detection
        </div>
        <h1 className="text-5xl sm:text-6xl font-black text-white tracking-tight mb-4" style={{ fontFamily: "'Georgia', serif" }}>
          ReviewGuard
        </h1>
        <p className="text-xl text-slate-300 mb-2">
          Fake Review Detection <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-sky-400">Powered by AI</span>
        </p>
        <p className="text-slate-400 text-sm max-w-2xl mx-auto leading-relaxed">
          Advanced multimodal ML system that analyzes text, metadata, and behavioral patterns to detect fake reviews with high accuracy.
        </p>
      </div>

      {/* Cards */}
      <div
        className="grid grid-cols-1 sm:grid-cols-2 gap-6 w-full max-w-3xl transition-all duration-700 delay-150"
        style={{ opacity: visible ? 1 : 0, transform: visible ? 'translateY(0)' : 'translateY(24px)' }}
      >
        {/* ReviewGuard - Main Product */}
        <button
          onClick={() => navigate('/reviewguard/login')}
          onMouseEnter={() => setHovered('rg')}
          onMouseLeave={() => setHovered(null)}
          className="group relative text-left rounded-2xl p-8 border-2 transition-all duration-300 overflow-hidden"
          style={{
            background: hovered === 'rg'
              ? 'linear-gradient(135deg, rgba(99,102,241,0.20) 0%, rgba(99,102,241,0.08) 100%)'
              : 'rgba(255,255,255,0.04)',
            borderColor: hovered === 'rg' ? 'rgba(99,102,241,0.7)' : 'rgba(255,255,255,0.1)',
            boxShadow: hovered === 'rg' ? '0 0 50px rgba(99,102,241,0.2)' : 'none',
            transform: hovered === 'rg' ? 'translateY(-4px)' : 'translateY(0)',
          }}
        >
          <div className="pointer-events-none absolute top-0 right-0 w-48 h-48 rounded-full opacity-20"
            style={{ background: 'radial-gradient(circle, #818cf8 0%, transparent 70%)', transform: 'translate(40%, -40%)' }} />

          {/* Main Product Badge */}
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-500/20 border border-indigo-400/40 text-[10px] font-bold text-indigo-300 uppercase tracking-wider mb-4">
            <span>⭐</span>
            <span>Core Product</span>
          </div>

          <div className="text-5xl mb-5">🛡️</div>

          <h2 className="text-2xl font-bold text-white mb-2" style={{ fontFamily: "'Georgia', serif" }}>
            ReviewGuard
          </h2>
          <p className="text-slate-300 text-sm leading-relaxed mb-6">
            Admin console for detecting and managing fake reviews using multimodal AI analysis. 
            Upload reviews, view detection results, and analyze patterns.
          </p>

          <div className="flex flex-wrap gap-1.5 mb-6">
            {['AI Detection', 'LIME/SHAP', 'Analytics', 'Bulk Upload'].map(tag => (
              <span key={tag} className="text-xs px-2.5 py-1 rounded-full text-indigo-200 border border-indigo-400/30 bg-indigo-900/40">
                {tag}
              </span>
            ))}
          </div>

          <div className="flex items-center gap-2 text-sm font-bold text-indigo-300 group-hover:text-indigo-200 transition">
            <span>Admin Console</span>
            <span className="transition-transform group-hover:translate-x-1 duration-200">→</span>
          </div>
        </button>

        {/* ShopTrust - Demo Environment */}
        <button
          onClick={() => navigate('/shoptrust/login')}
          onMouseEnter={() => setHovered('st')}
          onMouseLeave={() => setHovered(null)}
          className="group relative text-left rounded-2xl p-8 border-2 transition-all duration-300 overflow-hidden"
          style={{
            background: hovered === 'st'
              ? 'linear-gradient(135deg, rgba(14,165,233,0.18) 0%, rgba(14,165,233,0.08) 100%)'
              : 'rgba(255,255,255,0.04)',
            borderColor: hovered === 'st' ? 'rgba(14,165,233,0.7)' : 'rgba(255,255,255,0.1)',
            boxShadow: hovered === 'st' ? '0 0 50px rgba(14,165,233,0.2)' : 'none',
            transform: hovered === 'st' ? 'translateY(-4px)' : 'translateY(0)',
          }}
        >
          <div className="pointer-events-none absolute top-0 right-0 w-48 h-48 rounded-full opacity-20"
            style={{ background: 'radial-gradient(circle, #38bdf8 0%, transparent 70%)', transform: 'translate(40%, -40%)' }} />

          {/* Demo Badge */}
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-sky-500/20 border border-sky-400/40 text-[10px] font-bold text-sky-300 uppercase tracking-wider mb-4">
            <span>🎬</span>
            <span>Live Demo</span>
          </div>

          <div className="text-5xl mb-5">🛒</div>

          <h2 className="text-2xl font-bold text-white mb-2" style={{ fontFamily: "'Georgia', serif" }}>
            ShopTrust
          </h2>
          <p className="text-slate-300 text-sm leading-relaxed mb-6">
            Demo marketplace showing ReviewGuard in action. Browse products, write reviews, 
            and see real-time AI verification.
          </p>

          <div className="flex flex-wrap gap-1.5 mb-6">
            {['Live Demo', 'Real-time AI', 'Trust Scores', 'Interactive'].map(tag => (
              <span key={tag} className="text-xs px-2.5 py-1 rounded-full text-sky-200 border border-sky-400/30 bg-sky-900/40">
                {tag}
              </span>
            ))}
          </div>

          <div className="flex items-center gap-2 text-sm font-bold text-sky-300 group-hover:text-sky-200 transition">
            <span>Try Demo</span>
            <span className="transition-transform group-hover:translate-x-1 duration-200">→</span>
          </div>
        </button>
      </div>

      {/* Feature highlights */}
      <div
        className="mt-12 grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-3xl w-full transition-all duration-700 delay-300"
        style={{ opacity: visible ? 1 : 0 }}
      >
        <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-4 text-center">
          <div className="text-2xl mb-2">🧠</div>
          <div className="text-white font-semibold text-sm mb-1">Multimodal AI</div>
          <div className="text-slate-400 text-xs">Text + Metadata + Behavioral Analysis</div>
        </div>
        <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-4 text-center">
          <div className="text-2xl mb-2">🔍</div>
          <div className="text-white font-semibold text-sm mb-1">Explainable AI</div>
          <div className="text-slate-400 text-xs">LIME, SHAP, Attention Visualization</div>
        </div>
        <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-4 text-center">
          <div className="text-2xl mb-2">⚡</div>
          <div className="text-white font-semibold text-sm mb-1">Real-time Detection</div>
          <div className="text-slate-400 text-xs">Instant analysis and scoring</div>
        </div>
      </div>

      {/* Footer note */}
      <div
        className="mt-10 text-center transition-all duration-700 delay-400"
        style={{ opacity: visible ? 1 : 0 }}
      >
        <p className="text-xs text-slate-500 mb-3">
          Research project • FastAPI + React + PyTorch • PostgreSQL + MLflow
        </p>
        <p className="text-[10px] text-slate-600">
          Technologies: DistilBERT • XGBoost • Attention Fusion • Late Fusion
        </p>
      </div>
    </div>
  )
}
