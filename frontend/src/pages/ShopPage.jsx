import React, { useEffect, useState } from 'react'
import { apiFetch } from '../shop/shopApi'
import { NavBar, Toast } from '../shop/NavBar'
import AuthPage     from '../shop/AuthPage'
import HomePage     from '../shop/HomePage'
import ProductsPage from '../shop/ProductsPage'
import ExplorePage  from '../shop/ExplorePage'
import CartPage     from '../shop/CartPage'
import OrdersPage   from '../shop/OrdersPage'
import RankingsPage from '../shop/RankingsPage'
import FeedbackPage from '../shop/FeedbackPage'
import ReviewModal  from '../shop/ReviewModal'

export default function ShopPage({ user: propUser, navigate }) {
  const [page, setPage]                   = useState('home')
  const [user, setUser]                   = useState(propUser || null)
  const [cart, setCart]                   = useState(null)
  const [toast, setToast]                 = useState('')
  const [products, setProducts]           = useState([])
  const [orderSuccess, setOrderSuccess]   = useState(null)
  const [reviewProduct, setReviewProduct] = useState(null)
  const [reviewOrder, setReviewOrder]     = useState(null)

  useEffect(() => { loadProducts(); if (user) loadCart() }, [user])
  useEffect(() => { if (propUser !== undefined) setUser(propUser) }, [propUser])
  useEffect(() => { if (user && user.role === 'Owner' && navigate) navigate('/shop/owner') }, [user])

  async function loadProducts() {
    try { setProducts(await apiFetch('/api/shop/products')) } catch {}
  }
  async function loadCart() {
    try { setCart(await apiFetch('/api/shop/cart')) } catch {}
  }
  function showToast(msg) { setToast(msg); setTimeout(() => setToast(''), 2500) }

  async function addToCart(productId) {
    if (!user) { showToast('Please sign in to add to cart'); setPage('auth'); return }
    try { await apiFetch(`/api/shop/cart/${productId}`, { method: 'POST' }); showToast('Added to cart! 🛒'); loadCart() }
    catch { showToast('Failed to add to cart') }
  }
  async function removeFromCart(productId) {
    try { await apiFetch(`/api/shop/cart/${productId}`, { method: 'DELETE' }); loadCart() } catch {}
  }
  async function placeOrder(payMethod) {
    try {
      const fd = new FormData()
      fd.append('payment_method', payMethod || 'card')
      const res = await apiFetch('/api/shop/orders', { method: 'POST', body: fd })
      setOrderSuccess(res); setCart(null); setPage('success'); showToast('Order placed! 🎉')
    } catch { showToast('Failed to place order') }
  }
  function handleAuth(userData) { setUser(userData); loadCart(); setPage('home'); showToast(`Welcome, ${userData.username}! 👋`) }
  function handleLogout() { localStorage.removeItem('fake_review_token'); setUser(null); setCart(null); window.location.href = '/' }

  const cartCount = cart?.items?.length || 0
  const orderReviewProduct = reviewOrder?.items?.[0]
    ? { id: reviewOrder.items[0].product_id, name: reviewOrder.items[0].product_name || 'Product', category: '' }
    : null

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <NavBar page={page} setPage={setPage} cartCount={cartCount} user={user} onLogout={handleLogout} />

      {page === 'auth'     && <AuthPage     onSuccess={handleAuth} setPage={setPage} />}
      {page === 'home'     && <HomePage     setPage={setPage} user={user} products={products} onAddCart={addToCart} onViewReviews={setReviewProduct} />}
      {page === 'products' && <ProductsPage user={user} setPage={setPage} onAddCart={addToCart} onViewReviews={setReviewProduct} />}
      {page === 'explore'  && <ExplorePage  onAddCart={addToCart} onViewReviews={setReviewProduct} />}
      {page === 'cart'     && <CartPage     cart={cart} onRemove={removeFromCart} onOrder={placeOrder} setPage={setPage} />}
      {page === 'orders'   && <OrdersPage   user={user} setPage={setPage} onWriteReview={order => setReviewOrder(order)} />}
      {page === 'rankings' && <RankingsPage />}
      {page === 'feedback' && <FeedbackPage />}

      {page === 'success' && (
        <div className="max-w-md mx-auto p-10 text-center">
          <div className="text-6xl mb-4">✅</div>
          <div className="text-2xl font-bold text-slate-800 mb-2">Order placed!</div>
          <div className="text-slate-500 mb-4">Your order has been confirmed and will be delivered in 2–5 business days.</div>
          {orderSuccess && (
            <div className="bg-slate-100 rounded-xl px-5 py-4 mb-5 text-left">
              <div className="text-xs text-slate-400 mb-1">Order ID</div>
              <div className="font-mono font-bold text-slate-800">#{(orderSuccess.order_id || orderSuccess.id || '000001').toString().padStart(6,'0')}</div>
            </div>
          )}
          <div className="flex gap-3 justify-center">
            <button onClick={() => setPage('orders')} className="px-5 py-2.5 bg-sky-400 text-[#0a1628] font-bold text-sm rounded-xl">View orders</button>
            <button onClick={() => setPage('home')}   className="px-5 py-2.5 border border-slate-300 text-slate-700 font-semibold text-sm rounded-xl">Continue shopping</button>
          </div>
        </div>
      )}

      {reviewProduct && <ReviewModal product={reviewProduct} user={user} setPage={setPage} onClose={() => setReviewProduct(null)} />}
      {reviewOrder && orderReviewProduct && <ReviewModal product={orderReviewProduct} user={user} setPage={setPage} onClose={() => setReviewOrder(null)} />}

      <Toast msg={toast} />
    </div>
  )
}
