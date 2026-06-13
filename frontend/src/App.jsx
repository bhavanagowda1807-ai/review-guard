import React, { useEffect, useState } from 'react'
import UploadAdvanced from './components/UploadAdvanced'
import ShopPage from './pages/ShopPage'
import OwnerDashboard from './pages/OwnerDashboard'
import AdminDashboard from './pages/AdminDashboard'
import AdminDashboardCharts from './pages/AdminDashboardCharts'
import LandingPage from './pages/LandingPage'
import ReviewGuardLogin from './pages/ReviewGuardLogin'
import ShopTrustLogin from './pages/ShopTrustLogin'
import { getMe, logout } from './services/api'

function getPage() {
  const path = window.location.pathname
  if (path.startsWith('/admin/charts')) return 'admincharts'
  if (path.startsWith('/admin')) return 'admin'
  if (path.includes('/shop/owner')) return 'owner'
  if (path.startsWith('/shop')) return 'shop'
  if (path.startsWith('/reviewguard/login')) return 'rg-login'
  if (path.startsWith('/shoptrust/login')) return 'st-login'
  if (path.startsWith('/reviewguard')) return 'reviewguard'
  return 'landing'
}

export default function App() {
  const [page, setPage] = useState(getPage())
  const [user, setUser] = useState(null)
  const [userLoading, setUserLoading] = useState(true)

  useEffect(() => {
    // If landing on ShopTrust login, clear any admin token first
    if (getPage() === 'st-login') {
      localStorage.removeItem('fake_review_token')
      setUserLoading(false)
      return
    }
    getMe().then(setUser).catch(() => setUser(null)).finally(() => setUserLoading(false))
  }, [])

  useEffect(() => {
    const handler = () => {
      const newPage = getPage()
      // When navigating to ShopTrust login, clear admin token immediately
      if (newPage === 'st-login') {
        localStorage.removeItem('fake_review_token')
        setUser(null)
      }
      setPage(newPage)
    }
    window.addEventListener('popstate', handler)
    return () => window.removeEventListener('popstate', handler)
  }, [])

  function navigate(path) {
    // If going to ShopTrust login, clear admin token immediately
    if (path === '/shoptrust/login') {
      localStorage.removeItem('fake_review_token')
      setUser(null)
    }
    window.history.pushState({}, '', path)
    setPage(getPage())
  }

  function handleLogout() {
    logout()
    setUser(null)
    navigate('/')
  }

  function handleAdminLogin(u) {
    setUser(u)
    navigate('/admin')
  }

  function handleShopLogin(u) {
    setUser(u)
    if (u.role === 'Owner') {
      navigate('/shop/owner')
    } else {
      navigate('/shop')
    }
  }

  // Auth gates
  if (page === 'rg-login') return <ReviewGuardLogin onLogin={handleAdminLogin} navigate={navigate} />
  if (page === 'st-login') return <ShopTrustLogin onLogin={handleShopLogin} navigate={navigate} />

  // If landing, always show landing
  if (page === 'landing') return <LandingPage navigate={navigate} />

  // Shop pages
  if (page === 'shop') {
    if (!userLoading && user?.is_admin) { navigate('/reviewguard/login'); return null }
    if (!userLoading && user?.role === 'Owner') { navigate('/shop/owner'); return null }
    return <ShopPage user={user} navigate={navigate} />
  }
  if (page === 'owner') {
    if (!userLoading && user?.is_admin) { navigate('/reviewguard/login'); return null }
    if (!userLoading && user && user.role !== 'Owner') { navigate('/shop'); return null }
    return <OwnerDashboard user={user} navigate={navigate} />
  }

  // Admin pages — require admin user
  if (page === 'admin') {
    if (!userLoading && !user?.is_admin) { navigate('/reviewguard/login'); return null }
    return (
      <AdminDashboard
        user={user}
        navigate={navigate}
        onLogout={handleLogout}
      />
    )
  }
  if (page === 'admincharts') {
    if (!userLoading && !user?.is_admin) { navigate('/reviewguard/login'); return null }
    return (
      <AdminDashboardCharts
        user={user}
        navigate={navigate}
        onLogout={handleLogout}
      />
    )
  }

  // ReviewGuard home (upload / detect tool) — admin only
  if (page === 'reviewguard') {
    if (!userLoading && !user?.is_admin) { navigate('/reviewguard/login'); return null }
    return (
      <div className="min-h-screen bg-[#090b12] text-slate-100">
        <div className="border-b border-white/10 bg-[#0d111b]">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-3">
            <div className="flex items-center gap-3">
              <button onClick={() => navigate('/')} className="text-slate-500 hover:text-slate-300 text-sm transition">← Home</button>
              <div>
                <h1 className="text-lg font-semibold">🛡️ ReviewGuard</h1>
                <p className="text-xs text-slate-400">Fake Review Detection · Admin Console</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={() => navigate('/admin')} className="text-sm text-slate-400 hover:text-red-400 px-3 py-1.5 rounded-lg hover:bg-white/5 transition">⚙️ Admin</button>
              <button onClick={() => navigate('/admin/charts')} className="text-sm text-slate-400 hover:text-purple-400 px-3 py-1.5 rounded-lg hover:bg-white/5 transition">📊 Analytics</button>
              {!userLoading && user && (
                <div className="flex items-center gap-2 ml-1">
                  <span className="text-sm text-slate-300">👑 {user.username}</span>
                  <button onClick={handleLogout} className="text-xs bg-slate-700 hover:bg-slate-600 px-3 py-1.5 rounded-lg transition">Logout</button>
                </div>
              )}
            </div>
          </div>
        </div>
        <div className="mx-auto max-w-7xl p-5">
          <UploadAdvanced user={user} onAuthChange={setUser} />
        </div>
      </div>
    )
  }

  // Fallback
  return <LandingPage navigate={navigate} />
}
