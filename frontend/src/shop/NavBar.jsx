import React from 'react'

export function Toast({ msg }) {
  return msg ? (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-[#0f1e35] text-white px-5 py-2.5 rounded-xl text-sm font-semibold shadow-xl border border-white/10">
      {msg}
    </div>
  ) : null
}

export function NavBar({ page, setPage, cartCount, user, onLogout }) {
  const navItems = [
    { id: 'home',     label: 'Home' },
    { id: 'products', label: 'Browse' },
    { id: 'explore',  label: 'Explore' },
    { id: 'orders',   label: 'My Orders' },
    { id: 'rankings', label: 'Rankings' },
    { id: 'feedback', label: 'Feedback' },
  ]
  return (
    <>
      <nav className="sticky top-0 z-40 bg-[#0a1628] border-b border-white/10 shadow-lg">
        <div className="max-w-7xl mx-auto px-5 h-14 flex items-center justify-between gap-4">
          <button onClick={() => setPage('home')} className="flex items-center gap-2 font-bold text-white text-lg shrink-0">
            <span className="w-2 h-2 rounded-full bg-sky-400 inline-block" />ShopTrust
            <span className="ml-2 text-[10px] font-bold px-2 py-1 rounded-full bg-blue-500/20 text-blue-300 border border-blue-400/30 hidden sm:inline-block">
              DEMO
            </span>
          </button>
          <div className="flex items-center gap-0.5 overflow-x-auto hide-scrollbar">
            {navItems.map(({ id, label }) => (
              <button key={id} onClick={() => setPage(id)}
                className={`px-3 py-1.5 rounded-md text-sm font-medium whitespace-nowrap transition ${page === id ? 'bg-white/15 text-white' : 'text-white/70 hover:text-white hover:bg-white/10'}`}>
                {label}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button onClick={() => setPage('cart')}
              className="relative flex items-center gap-1.5 px-3 py-1.5 bg-white/10 border border-white/20 rounded-md text-sm font-semibold text-white hover:bg-white/15 transition">
              🛒 Cart
              {cartCount > 0 && (
                <span className="absolute -top-1.5 -right-1.5 bg-sky-400 text-[#0a1628] text-[9px] font-black w-4 h-4 rounded-full flex items-center justify-center">{cartCount}</span>
              )}
            </button>
            {user ? (
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-white/10 border border-white/20 rounded-full">
                  <span className="w-5 h-5 rounded-full bg-sky-400 text-[#0a1628] text-[10px] font-black flex items-center justify-center">{(user.username || 'U')[0].toUpperCase()}</span>
                  <span className="text-sm font-semibold text-white/90 max-w-[80px] truncate">{user.username}</span>
                </div>
                <button onClick={onLogout} className="px-3 py-1.5 bg-red-700/80 hover:bg-red-600 text-white text-xs font-bold rounded-md transition">Sign out</button>
              </div>
            ) : (
              <button onClick={() => setPage('auth')} className="px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white text-sm font-bold rounded-md transition">Sign In</button>
            )}
          </div>
        </div>
      </nav>
      
      {/* ReviewGuard Branding Bar */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 border-b border-blue-700">
        <div className="max-w-7xl mx-auto px-5 py-2 flex items-center justify-between text-white text-xs">
          <div className="flex items-center gap-2">
            <span className="text-base">🛡️</span>
            <span className="font-semibold">Powered by ReviewGuard</span>
            <span className="hidden sm:inline text-white/70">• All reviews AI-verified for authenticity</span>
          </div>
          <button 
            onClick={() => window.location.href = '/reviewguard/login'}
            className="px-3 py-1 bg-white/20 hover:bg-white/30 rounded-md font-semibold text-[11px] transition border border-white/30"
          >
            Admin Console →
          </button>
        </div>
      </div>
    </>
  )
}
