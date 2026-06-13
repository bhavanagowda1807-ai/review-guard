import React, {useEffect, useState} from 'react'
import {LogIn, LogOut, UserPlus} from 'lucide-react'
import {getMe, login, logout, register} from '../services/api'

export default function AuthPanel({onAuthChange}){
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [user, setUser] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    getMe().then(setUser).catch(() => setUser(null))
  }, [])

  const authenticate = async (mode) => {
    setBusy(true)
    try {
      if (mode === 'register') await register(username, password)
      await login(username, password)
      const me = await getMe()
      setUser(me)
      onAuthChange?.()
    } finally {
      setBusy(false)
    }
  }

  const signOut = () => {
    logout()
    setUser(null)
    onAuthChange?.()
  }

  return (
    <div className="rounded border border-white/10 bg-[#111827] p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="font-semibold">Workspace Login</div>
        {user && <button onClick={signOut} className="inline-flex items-center gap-1 rounded bg-white/10 px-2 py-1 text-xs text-slate-300"><LogOut size={13}/> Logout</button>}
      </div>
      {user ? (
        <div className="text-sm text-slate-300">Signed in as <span className="text-slate-100">{user.username}</span></div>
      ) : (
        <div className="grid gap-2">
          <input value={username} onChange={e=>setUsername(e.target.value)} placeholder="Username" className="rounded border border-white/10 bg-[#111827] px-3 py-2 text-sm outline-none focus:border-indigo-400" />
          <input value={password} onChange={e=>setPassword(e.target.value)} placeholder="Password" type="password" className="rounded border border-white/10 bg-[#111827] px-3 py-2 text-sm outline-none focus:border-indigo-400" />
          <div className="flex gap-2">
            <button disabled={busy || !username || !password} onClick={() => authenticate('login')} className="inline-flex items-center gap-2 rounded bg-indigo-500 px-3 py-2 text-sm text-white disabled:opacity-60"><LogIn size={15}/> Login</button>
            <button disabled={busy || !username || !password} onClick={() => authenticate('register')} className="inline-flex items-center gap-2 rounded bg-white/10 px-3 py-2 text-sm text-slate-200 disabled:opacity-60"><UserPlus size={15}/> Register</button>
          </div>
        </div>
      )}
    </div>
  )
}
