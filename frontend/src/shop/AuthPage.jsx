import React, { useState } from 'react'
import { API_BASE } from './shopApi'

export default function AuthPage({ onSuccess, setPage }) {
  const [tab, setTab] = useState('login')
  const [role, setRole] = useState(null)
  const [form, setForm] = useState({ username: '', email: '', full_name: '', password: '', phone: '', age: '', gender: 'Other' })
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)

  if (!role) return (
    <div className="min-h-[80vh] flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="text-3xl font-bold text-white mb-1">ShopTrust</div>
          <div className="text-sm text-slate-400">Choose how you'd like to continue</div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          {[
            { id: 'user',  icon: '🛍️', name: 'Customer', sub: 'Browse & buy products' },
            { id: 'owner', icon: '🏪', name: 'Seller',   sub: 'Manage your store' },
          ].map(r => (
            <button key={r.id} onClick={() => setRole(r.id)}
              className="p-5 rounded-2xl border-2 border-white/10 hover:border-sky-400/50 bg-white/5 text-center transition">
              <div className="text-3xl mb-2">{r.icon}</div>
              <div className="font-bold text-white text-sm">{r.name}</div>
              <div className="text-xs text-slate-400 mt-1">{r.sub}</div>
            </button>
          ))}
        </div>
        <button onClick={() => setPage('home')} className="mt-6 w-full text-sm text-slate-500 hover:text-slate-300 transition">
          ← Back to shop
        </button>
      </div>
    </div>
  )

  const isOwner = role === 'owner'
  const f = (k, v) => setForm(prev => ({ ...prev, [k]: v }))

  async function submit() {
    setErr(''); setLoading(true)
    try {
      if (tab === 'register') {
        if (!form.username || !form.password) { setErr('Username and password are required.'); setLoading(false); return }
        if (form.password.length < 8) { setErr('Password must be at least 8 characters.'); setLoading(false); return }
        const regRes = await fetch(`${API_BASE}/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: form.username, password: form.password }),
        })
        const regData = await regRes.json()
        if (!regRes.ok) { setErr(regData.detail || 'Registration failed'); setLoading(false); return }
        setTab('login'); setErr('Account created! Please sign in.')
        setForm(f => ({ ...f, password: '' })); setLoading(false); return
      }

      const formBody = new URLSearchParams()
      formBody.append('username', form.username)
      formBody.append('password', form.password)
      const loginRes = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formBody.toString(),
      })
      const loginData = await loginRes.json()
      if (!loginRes.ok) { setErr(loginData.detail || 'Invalid username or password'); setLoading(false); return }

      localStorage.setItem('fake_review_token', loginData.access_token)
      const meRes = await fetch(`${API_BASE}/auth/me`, { headers: { Authorization: `Bearer ${loginData.access_token}` } })
      const me = meRes.ok ? await meRes.json() : { username: form.username }
      onSuccess(me, isOwner)
    } catch { setErr('Connection error. Is the backend running?') }
    setLoading(false)
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center p-4 bg-gradient-to-br from-[#0a1628] via-[#0d2240] to-[#1a3a6e]">
      <div className="w-full max-w-sm bg-slate-100 rounded-2xl p-7 shadow-2xl">
        <div className="text-center mb-5">
          <div className="text-2xl font-bold text-[#0a1628]">ShopTrust</div>
          <div className="text-xs text-slate-500">{isOwner ? 'Owner / Seller Portal' : 'Customer Portal'}</div>
        </div>
        <div className="flex bg-slate-200 rounded-lg p-1 mb-5">
          {['login', 'register'].map(t => (
            <button key={t} onClick={() => { setTab(t); setErr('') }}
              className={`flex-1 py-2 text-xs font-bold rounded-md transition ${tab === t ? 'bg-sky-400 text-[#0a1628]' : 'text-slate-500'}`}>
              {t === 'login' ? 'Sign In' : 'Register'}
            </button>
          ))}
        </div>
        <div className="space-y-3">
          {tab === 'register' && <>
            <input value={form.full_name} onChange={e => f('full_name', e.target.value)}
              placeholder={isOwner ? 'Shop name *' : 'Full name *'}
              className="w-full px-3 py-2.5 text-sm bg-slate-200 border border-slate-300 rounded-lg text-slate-800 outline-none focus:border-sky-400" />
            <input value={form.email} onChange={e => f('email', e.target.value)} placeholder="Email *" type="email"
              className="w-full px-3 py-2.5 text-sm bg-slate-200 border border-slate-300 rounded-lg text-slate-800 outline-none focus:border-sky-400" />
            {!isOwner && (
              <div className="grid grid-cols-2 gap-2">
                <input value={form.phone} onChange={e => f('phone', e.target.value)} placeholder="Phone (optional)"
                  className="px-3 py-2.5 text-sm bg-slate-200 border border-slate-300 rounded-lg text-slate-800 outline-none focus:border-sky-400" />
                <input value={form.age} onChange={e => f('age', e.target.value)} placeholder="Age" type="number"
                  className="px-3 py-2.5 text-sm bg-slate-200 border border-slate-300 rounded-lg text-slate-800 outline-none focus:border-sky-400" />
              </div>
            )}
          </>}
          <input value={form.username} onChange={e => f('username', e.target.value)} placeholder="Username *"
            className="w-full px-3 py-2.5 text-sm bg-slate-200 border border-slate-300 rounded-lg text-slate-800 outline-none focus:border-sky-400" />
          <input value={form.password} onChange={e => f('password', e.target.value)} placeholder="Password *" type="password"
            className="w-full px-3 py-2.5 text-sm bg-slate-200 border border-slate-300 rounded-lg text-slate-800 outline-none focus:border-sky-400"
            onKeyDown={e => e.key === 'Enter' && submit()} />
        </div>
        {err && <div className="mt-3 text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">{err}</div>}
        <button onClick={submit} disabled={loading}
          className="mt-4 w-full py-3 bg-[#0a1628] hover:bg-[#0d2240] text-white font-bold rounded-lg text-sm transition disabled:opacity-50">
          {loading ? 'Please wait...' : tab === 'login' ? 'Sign In →' : 'Create Account →'}
        </button>
        <button onClick={() => { setRole(null); setErr('') }} className="mt-3 w-full text-xs text-slate-400 hover:text-slate-600 transition">
          ← Back to role selection
        </button>
      </div>
    </div>
  )
}
