import React, { useEffect, useState } from 'react'
import { apiFetch } from './shopApi'

// Status badge config for all order states
const STATUS_CFG = {
  pending:    { cls: 'bg-yellow-100 text-yellow-700',  label: '⏳ Pending',     canCancel: true },
  processing: { cls: 'bg-blue-100 text-blue-700',      label: '⚙️ Processing',  canCancel: true },
  shipped:    { cls: 'bg-purple-100 text-purple-700',   label: '📦 Shipped',    canCancel: false },
  delivered:  { cls: 'bg-green-100 text-green-700',    label: '✅ Delivered',   canCancel: false },
  cancelled:  { cls: 'bg-red-100 text-red-500',        label: '✖ Cancelled',   canCancel: false },
  completed:  { cls: 'bg-green-100 text-green-700',    label: '✅ Delivered',   canCancel: false },
}

// Delivery progress stepper
const STEPS = ['pending', 'processing', 'shipped', 'delivered']
function OrderStepper({ status }) {
  const s = (status || 'pending').toLowerCase()
  const activeIdx = STEPS.indexOf(s)
  if (s === 'cancelled') return (
    <div className="mt-3 text-xs text-red-500 font-semibold">✖ This order was cancelled</div>
  )
  return (
    <div className="mt-3 flex items-center gap-0">
      {STEPS.map((step, i) => {
        const done = activeIdx > i
        const active = activeIdx === i
        const stepLabel = { pending: 'Placed', processing: 'Processing', shipped: 'Shipped', delivered: 'Delivered' }
        return (
          <React.Fragment key={step}>
            <div className="flex flex-col items-center">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold border-2 ${
                done ? 'bg-[#0a1628] border-[#0a1628] text-white'
                : active ? 'bg-sky-500 border-sky-500 text-white'
                : 'bg-white border-slate-300 text-slate-400'
              }`}>
                {done ? '✓' : i + 1}
              </div>
              <div className={`text-[9px] mt-0.5 font-semibold ${active ? 'text-sky-500' : done ? 'text-slate-600' : 'text-slate-300'}`}>
                {stepLabel[step]}
              </div>
            </div>
            {i < STEPS.length - 1 && (
              <div className={`flex-1 h-0.5 mb-4 mx-1 ${done ? 'bg-[#0a1628]' : 'bg-slate-200'}`} />
            )}
          </React.Fragment>
        )
      })}
    </div>
  )
}

export default function OrdersPage({ user, setPage, onWriteReview }) {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [cancelling, setCancelling] = useState(null)

  useEffect(() => { load() }, [])

  async function load() {
    setLoading(true)
    try { setOrders(await apiFetch('/api/shop/orders')) } catch { setOrders([]) }
    setLoading(false)
  }

  async function cancelOrder(orderId) {
    setCancelling(orderId)
    try {
      await apiFetch(`/api/shop/orders/${orderId}/cancel`, { method: 'POST' })
      await load()
    } catch (e) {
      alert(e?.message || 'Could not cancel order')
    }
    setCancelling(null)
  }

  if (!user) return (
    <div className="text-center py-20 text-slate-400">
      <div>Please sign in to view your orders</div>
      <button onClick={() => setPage('auth')} className="mt-4 px-5 py-2 bg-[#0a1628] text-white text-sm font-bold rounded-xl">Sign In</button>
    </div>
  )

  return (
    <div className="p-5 max-w-4xl mx-auto">
      <h2 className="text-xl font-bold text-slate-800 mb-5">My Orders</h2>
      {loading
        ? <div className="text-slate-400 text-center py-20">Loading…</div>
        : orders.length === 0
          ? <div className="text-slate-400 text-center py-20">No orders yet. Start shopping!</div>
          : <div className="space-y-4">
              {orders.map(order => {
                const statusKey = (order.status || 'pending').toLowerCase()
                const cfg = STATUS_CFG[statusKey] || STATUS_CFG.pending
                const isDelivered = statusKey === 'delivered' || statusKey === 'completed'
                return (
                  <div key={order.order_id || order.id} className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-sm font-bold text-slate-700">
                          #{(order.order_id || order.id)?.toString().padStart(6, '0')}
                        </span>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${cfg.cls}`}>
                          {cfg.label}
                        </span>
                      </div>
                      <div className="text-sm text-slate-400">
                        {(order.ordered_at || order.created_at)
                          ? new Date(order.ordered_at || order.created_at).toLocaleDateString()
                          : ''}
                      </div>
                    </div>

                    {/* Progress stepper */}
                    <OrderStepper status={order.status} />

                    <div className="font-bold text-slate-800 mt-3">
                      ₹{(order.total_amount || order.total)?.toLocaleString()}
                    </div>

                    {order.items && order.items.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {order.items.map((item, i) => (
                          <div key={i} className="text-xs text-slate-500 flex items-center gap-1">
                            <span className="text-slate-300">•</span>
                            <span>{item.product_name || item.name || 'Product'}</span>
                            <span className="text-slate-300">×{item.qty || item.quantity || 1}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    <div className="mt-3 flex flex-wrap gap-2">
                      {isDelivered && (
                        <button
                          onClick={() => onWriteReview(order)}
                          className="px-4 py-1.5 bg-sky-500 hover:bg-sky-400 text-white text-xs font-bold rounded-lg transition">
                          ✍️ Write a Review
                        </button>
                      )}
                      {cfg.canCancel && (
                        <button
                          disabled={cancelling === (order.order_id || order.id)}
                          onClick={() => {
                            if (window.confirm('Cancel this order?')) cancelOrder(order.order_id || order.id)
                          }}
                          className="px-4 py-1.5 bg-red-50 hover:bg-red-100 text-red-600 border border-red-200 text-xs font-bold rounded-lg transition disabled:opacity-50">
                          {cancelling === (order.order_id || order.id) ? 'Cancelling…' : '✖ Cancel Order'}
                        </button>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
      }
    </div>
  )
}
