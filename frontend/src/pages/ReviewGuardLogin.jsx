import React, { useState, useEffect } from 'react'
import { login, getMe } from '../services/api'

export default function ReviewGuardLogin({ onLogin, navigate }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 60)
    return () => clearTimeout(t)
  }, [])

  async function handleSubmit() {
    if (!username || !password) { setError('Please enter your credentials'); return }
    setLoading(true)
    setError('')
    try {
      await login(username, password)
      const me = await getMe()
      if (!me.is_admin) {
        setError('Access denied. ReviewGuard is restricted to administrators only.')
        localStorage.removeItem('fake_review_token')
        setLoading(false)
        return
      }
      onLogin(me)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Invalid credentials')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#07090f] flex flex-col items-center justify-center p-6 relative overflow-hidden">

      {/* Background */}
      <div className="pointer-events-none absolute inset-0" style={{
        backgroundImage: 'linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)',
        backgroundSize: '48px 48px',
      }} />
      <div className="pointer-events-none absolute -top-60 left-1/2 -translate-x-1/2 w-[600px] h-[400px] rounded-full"
        style={{ background: 'radial-gradient(ellipse, rgba(99,102,241,0.12) 0%, transparent 70%)' }} />

      {/* Back button */}
      <button
        onClick={() => navigate('/')}
        className="absolute top-5 left-5 flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-300 transition"
      >
        ← Back
      </button>

      <div
        className="w-full max-w-sm transition-all duration-700"
        style={{ opacity: visible ? 1 : 0, transform: visible ? 'translateY(0)' : 'translateY(20px)' }}
      >
        {/* Logo */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4 border border-indigo-500/30"
            style={{ background: 'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(99,102,241,0.05))' }}>
            <span className="text-3xl">🛡️</span>
          </div>
          <h1 className="text-2xl font-black text-white mb-1" style={{ fontFamily: "'Georgia', serif" }}>
            ReviewGuard
          </h1>
          <p className="text-slate-400 text-sm">Administrator access only</p>
          <div className="inline-flex items-center gap-1.5 mt-3 px-3 py-1 rounded-full border border-indigo-400/20 bg-indigo-900/20 text-xs text-indigo-300">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 inline-block" />
            Restricted Portal
          </div>
        </div>

        {/* Form */}
        <div className="rounded-2xl border border-white/8 p-7"
          style={{ background: 'rgba(255,255,255,0.03)', backdropFilter: 'blur(12px)' }}>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Admin Username
              </label>
              <input
                value={username}
                onChange={e => setUsername(e.target.value)}
                placeholder="Enter admin username"
                className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-3 text-slate-100 text-sm outline-none focus:border-indigo-500/70 focus:bg-slate-900 transition placeholder-slate-600"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Password
              </label>
              <input
                value={password}
                onChange={e => setPassword(e.target.value)}
                type="password"
                placeholder="Enter password"
                className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-3 text-slate-100 text-sm outline-none focus:border-indigo-500/70 focus:bg-slate-900 transition placeholder-slate-600"
                onKeyDown={e => e.key === 'Enter' && handleSubmit()}
              />
            </div>
          </div>

          {error && (
            <div className="mt-4 flex items-start gap-2.5 text-sm text-red-300 bg-red-900/20 border border-red-500/20 rounded-xl px-4 py-3">
              <span className="mt-0.5 shrink-0">⚠️</span>
              <span>{error}</span>
            </div>
          )}

          <button
            onClick={handleSubmit}
            disabled={loading}
            className="mt-6 w-full py-3 rounded-xl text-sm font-bold text-white transition-all duration-200 disabled:opacity-50"
            style={{
              background: loading ? 'rgba(99,102,241,0.5)' : 'linear-gradient(135deg, #6366f1, #4f46e5)',
              boxShadow: loading ? 'none' : '0 4px 24px rgba(99,102,241,0.3)',
            }}
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
                Verifying…
              </span>
            ) : '🔐 Access Admin Console'}
          </button>
        </div>

        <p className="text-center text-xs text-slate-600 mt-5">
          Not an admin?{' '}
          <button onClick={() => navigate('/shoptrust/login')} className="text-sky-500 hover:text-sky-400 transition">
            Go to ShopTrust →
          </button>
        </p>
      </div>
    </div>
  )
}
