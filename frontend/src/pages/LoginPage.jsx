import React, { useState } from 'react'
import { login, register, getMe } from '../services/api'

export default function LoginPage({ onLogin, navigate }) {
  const [mode, setMode] = useState('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('User')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit() {
    if (!username || !password) { setError('Please fill all fields'); return }
    setLoading(true)
    setError('')
    try {
      if (mode === 'register') {
        await register(username, password, role)
      }
      await login(username, password)
      const me = await getMe()
      onLogin(me)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Invalid credentials')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#090b12] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-slate-100">🛡️ ReviewGuard</h1>
          <p className="text-slate-400 text-sm mt-1">Multimodal Fake Review Detection</p>
        </div>

        <div className="bg-[#0d111b] border border-white/10 rounded-2xl p-8">
          {/* Tabs */}
          <div className="flex gap-1 bg-slate-800/50 rounded-lg p-1 mb-6">
            {['login', 'register'].map(m => (
              <button
                key={m}
                onClick={() => { setMode(m); setError('') }}
                className={`flex-1 py-2 text-sm font-medium rounded-md transition ${
                  mode === m ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {m === 'login' ? '🔑 Login' : '✨ Register'}
              </button>
            ))}
          </div>

          <div className="space-y-4">
            {/* Role selector shown on BOTH login and register */}
            <div>
              <label className="text-sm text-slate-400 mb-2 block">Role</label>
              <div className="grid grid-cols-3 gap-2">
                {['User', 'Owner', 'Admin'].map(r => (
                  <button
                    key={r}
                    onClick={() => setRole(r)}
                    className={`py-2 text-sm font-medium rounded-lg border transition ${
                      role === r
                        ? 'bg-indigo-600 border-indigo-600 text-white'
                        : 'border-white/10 text-slate-400 hover:border-white/20'
                    }`}
                  >
                    {r === 'User' ? '👤' : r === 'Owner' ? '🏪' : '👑'} {r}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-sm text-slate-400 mb-1 block">Username</label>
              <input
                value={username}
                onChange={e => setUsername(e.target.value)}
                placeholder="Enter username"
                className="w-full bg-slate-800 border border-white/10 rounded-lg px-4 py-3 text-slate-100 text-sm outline-none focus:border-indigo-500 transition"
              />
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">Password</label>
              <input
                value={password}
                onChange={e => setPassword(e.target.value)}
                type="password"
                placeholder="Enter password"
                className="w-full bg-slate-800 border border-white/10 rounded-lg px-4 py-3 text-slate-100 text-sm outline-none focus:border-indigo-500 transition"
                onKeyDown={e => e.key === 'Enter' && handleSubmit()}
              />
            </div>
          </div>

          {error && (
            <div className="mt-4 text-sm text-red-400 bg-red-900/20 border border-red-500/20 rounded-lg px-4 py-3">
              {error}
            </div>
          )}

          <button
            onClick={handleSubmit}
            disabled={loading}
            className="mt-6 w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold py-3 rounded-xl text-sm transition"
          >
            {loading ? 'Please wait…' : mode === 'login' ? '🔑 Login' : '✨ Create Account'}
          </button>

          <div className="mt-4 text-center">
            <button onClick={() => navigate('/shop')}
              className="text-sm text-sky-400 hover:text-sky-300 transition">
              🛒 Go to ShopTrust →
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
