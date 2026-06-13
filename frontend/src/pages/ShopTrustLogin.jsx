import React, { useState, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function ShopTrustLogin({ onLogin, navigate }) {
  const [role, setRole] = useState(null) // null | 'user' | 'owner'
  const [tab, setTab] = useState('login') // 'login' | 'register'
  const [form, setForm] = useState({ username: '', email: '', full_name: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 60)
    return () => clearTimeout(t)
  }, [])

  function resetForm() {
    setForm({ username: '', email: '', full_name: '', password: '' })
    setError('')
    setTab('login')
  }

  async function handleSubmit() {
    if (!form.username || !form.password) { setError('Username and password are required'); return }
    setLoading(true); setError('')
    try {
      if (tab === 'register') {
        if (form.password.length < 8) { setError('Password must be at least 8 characters'); setLoading(false); return }
        const apiRole = role === 'owner' ? 'Owner' : 'User'
        const regRes = await fetch(`${API_BASE}/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: form.username, password: form.password, email: form.email || undefined, full_name: form.full_name || undefined, role: apiRole }),
        })
        if (!regRes.ok) {
          const d = await regRes.json().catch(() => ({}))
          throw new Error(d.detail || 'Registration failed')
        }
      }

      // Login
      const fd = new URLSearchParams()
      fd.append('username', form.username)
      fd.append('password', form.password)
      const loginRes = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: fd,
      })
      if (!loginRes.ok) {
        const d = await loginRes.json().catch(() => ({}))
        throw new Error(d.detail || 'Invalid credentials')
      }
      const { access_token } = await loginRes.json()
      localStorage.setItem('fake_review_token', access_token)

      const meRes = await fetch(`${API_BASE}/auth/me`, { headers: { Authorization: `Bearer ${access_token}` } })
      const me = await meRes.json()

      if (me.is_admin) {
        setError('Admin accounts must use the ReviewGuard portal.')
        localStorage.removeItem('fake_review_token')
        setLoading(false)
        return
      }

      onLogin(me)
      if (me.role === 'Owner' || role === 'owner') {
        navigate('/shop/owner')
      } else {
        navigate('/shop')
      }
    } catch (err) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const isOwner = role === 'owner'
  const accentColor = isOwner ? '#0ea5e9' : '#34d399'
  const accentGlow = isOwner ? 'rgba(14,165,233,0.2)' : 'rgba(52,211,153,0.2)'
  const accentBorder = isOwner ? 'rgba(14,165,233,0.5)' : 'rgba(52,211,153,0.5)'

  return (
    <div className="min-h-screen bg-[#07090f] flex flex-col items-center justify-center p-6 relative overflow-hidden">

      {/* Background grid */}
      <div className="pointer-events-none absolute inset-0" style={{
        backgroundImage: 'linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)',
        backgroundSize: '48px 48px',
      }} />
      <div className="pointer-events-none absolute -top-60 left-1/2 -translate-x-1/2 w-[600px] h-[400px] rounded-full"
        style={{ background: `radial-gradient(ellipse, ${accentGlow} 0%, transparent 70%)`, transition: 'background 0.4s' }} />

      {/* Back button */}
      <button
        onClick={() => { if (role) { setRole(null); resetForm() } else navigate('/') }}
        className="absolute top-5 left-5 flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-300 transition"
      >
        ← {role ? 'Change role' : 'Back'}
      </button>

      <div
        className="w-full max-w-sm transition-all duration-700"
        style={{ opacity: visible ? 1 : 0, transform: visible ? 'translateY(0)' : 'translateY(20px)' }}
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4 border"
            style={{
              background: `linear-gradient(135deg, ${accentGlow}, transparent)`,
              borderColor: accentBorder,
              transition: 'all 0.4s',
            }}>
            <span className="text-3xl">{isOwner ? '🏪' : '🛒'}</span>
          </div>
          <h1 className="text-2xl font-black text-white mb-1" style={{ fontFamily: "'Georgia', serif" }}>
            ShopTrust
          </h1>
          <p className="text-slate-400 text-sm">
            {role ? (isOwner ? 'Seller Portal' : 'Customer Portal') : 'Trusted marketplace platform'}
          </p>
        </div>

        {/* Role selector */}
        {!role ? (
          <div
            className="transition-all duration-500"
            style={{ opacity: visible ? 1 : 0 }}
          >
            <p className="text-center text-xs text-slate-500 uppercase tracking-widest mb-4">
              I am a…
            </p>
            <div className="grid grid-cols-2 gap-4">
              {[
                { id: 'user', icon: '🛍️', name: 'Customer', sub: 'Browse & buy products' },
                { id: 'owner', icon: '🏪', name: 'Seller', sub: 'Manage your store' },
              ].map(r => (
                <button
                  key={r.id}
                  onClick={() => { setRole(r.id); resetForm() }}
                  className="p-5 rounded-2xl border text-center transition-all duration-200 hover:-translate-y-1 group"
                  style={{
                    background: 'rgba(255,255,255,0.03)',
                    borderColor: 'rgba(255,255,255,0.08)',
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.borderColor = r.id === 'owner' ? 'rgba(14,165,233,0.5)' : 'rgba(52,211,153,0.5)'
                    e.currentTarget.style.background = r.id === 'owner' ? 'rgba(14,165,233,0.07)' : 'rgba(52,211,153,0.07)'
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'
                    e.currentTarget.style.background = 'rgba(255,255,255,0.03)'
                  }}
                >
                  <div className="text-3xl mb-2">{r.icon}</div>
                  <div className="font-bold text-white text-sm">{r.name}</div>
                  <div className="text-xs text-slate-400 mt-1">{r.sub}</div>
                </button>
              ))}
            </div>
            <p className="text-center text-xs text-slate-600 mt-6">
              Admin?{' '}
              <button onClick={() => navigate('/reviewguard/login')} className="text-indigo-400 hover:text-indigo-300 transition">
                Use ReviewGuard →
              </button>
            </p>
          </div>
        ) : (
          /* Login / Register form */
          <div className="transition-all duration-500">
            {/* Role pill */}
            <div className="flex justify-center mb-5">
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border text-xs font-semibold"
                style={{ borderColor: accentBorder, color: accentColor, background: `${accentGlow}` }}>
                {isOwner ? '🏪 Seller' : '🛍️ Customer'}
              </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-1 bg-white/5 rounded-xl p-1 mb-5">
              {['login', 'register'].map(t => (
                <button
                  key={t}
                  onClick={() => { setTab(t); setError('') }}
                  className="flex-1 py-2 text-sm font-semibold rounded-lg transition"
                  style={tab === t
                    ? { background: accentColor, color: '#07090f' }
                    : { color: '#94a3b8' }
                  }
                >
                  {t === 'login' ? '🔑 Login' : '✨ Register'}
                </button>
              ))}
            </div>

            <div className="rounded-2xl border border-white/8 p-6"
              style={{ background: 'rgba(255,255,255,0.03)' }}>
              <div className="space-y-3">
                {tab === 'register' && (
                  <>
                    <div>
                      <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Full Name</label>
                      <input
                        value={form.full_name}
                        onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))}
                        placeholder="Optional"
                        className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-slate-100 text-sm outline-none focus:border-sky-500/60 transition placeholder-slate-600"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Email</label>
                      <input
                        value={form.email}
                        onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                        placeholder="Optional"
                        type="email"
                        className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-slate-100 text-sm outline-none focus:border-sky-500/60 transition placeholder-slate-600"
                      />
                    </div>
                  </>
                )}
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Username</label>
                  <input
                    value={form.username}
                    onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
                    placeholder="Enter username"
                    className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-slate-100 text-sm outline-none transition placeholder-slate-600"
                    style={{ '--tw-ring-color': accentColor }}
                    onFocus={e => e.target.style.borderColor = accentBorder}
                    onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.10)'}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Password</label>
                  <input
                    value={form.password}
                    onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                    type="password"
                    placeholder={tab === 'register' ? 'Min. 8 characters' : 'Enter password'}
                    className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-slate-100 text-sm outline-none transition placeholder-slate-600"
                    onFocus={e => e.target.style.borderColor = accentBorder}
                    onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.10)'}
                    onKeyDown={e => e.key === 'Enter' && handleSubmit()}
                  />
                </div>
              </div>

              {error && (
                <div className="mt-4 flex items-start gap-2 text-sm text-red-300 bg-red-900/20 border border-red-500/20 rounded-xl px-4 py-3">
                  <span className="shrink-0 mt-0.5">⚠️</span>
                  <span>{error}</span>
                </div>
              )}

              <button
                onClick={handleSubmit}
                disabled={loading}
                className="mt-5 w-full py-3 rounded-xl text-sm font-bold text-[#07090f] transition-all duration-200 disabled:opacity-50"
                style={{
                  background: loading ? accentColor + '80' : accentColor,
                  boxShadow: loading ? 'none' : `0 4px 24px ${accentGlow}`,
                }}
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                    </svg>
                    Please wait…
                  </span>
                ) : tab === 'login' ? `🔑 Sign In as ${isOwner ? 'Seller' : 'Customer'}` : `✨ Create ${isOwner ? 'Seller' : 'Customer'} Account`}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
