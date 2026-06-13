import React, { useState } from 'react'
import { catIcon } from './shopApi'

export default function CartPage({ cart, onRemove, onOrder, setPage }) {
  const [payMethod, setPayMethod] = useState('Card')
  const [addr, setAddr] = useState('')
  const [checkout, setCheckout] = useState(false)
  const [cardName, setCardName] = useState('')
  const [cardNum, setCardNum] = useState('')
  const [cardExp, setCardExp] = useState('')
  const [cardCvv, setCardCvv] = useState('')

  const total = cart?.total || 0
  const items = cart?.items || []

  if (checkout) return (
    <div className="max-w-3xl mx-auto p-5 grid grid-cols-1 md:grid-cols-[1fr_280px] gap-5">
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
        <div className="font-bold text-slate-800 text-lg mb-4">Payment details</div>
        <div className="flex gap-2 mb-5">
          {[['Card','💳'],['UPI','📱'],['Net Banking','🏦'],['COD','💵']].map(([m, ic]) => (
            <button key={m} onClick={() => setPayMethod(m)}
              className={`flex-1 py-2.5 rounded-xl text-xs font-bold border-2 transition ${payMethod === m ? 'border-sky-400 bg-sky-50 text-sky-700' : 'border-slate-200 text-slate-500'}`}>
              <div className="text-lg mb-0.5">{ic}</div>{m}
            </button>
          ))}
        </div>

        {payMethod === 'Card' && (
          <div className="space-y-3">
            <div className="bg-gradient-to-br from-[#0a1628] to-[#1e3f70] rounded-xl p-4 text-white mb-4">
              <div className="text-lg tracking-[0.2em] font-mono mb-3">{cardNum || '•••• •••• •••• ••••'}</div>
              <div className="flex justify-between text-xs">
                <span>{cardName || 'YOUR NAME'}</span>
                <span>{cardExp || 'MM/YY'}</span>
              </div>
            </div>
            <input value={cardName} onChange={e => setCardName(e.target.value)} placeholder="Cardholder name"
              className="w-full px-3 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-lg outline-none focus:border-sky-400" />
            <input value={cardNum} onChange={e => setCardNum(e.target.value.replace(/[^\d]/g,'').replace(/(.{4})/g,'$1 ').trim())}
              placeholder="1234 5678 9012 3456" maxLength={19}
              className="w-full px-3 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-lg outline-none focus:border-sky-400" />
            <div className="grid grid-cols-2 gap-3">
              <input value={cardExp} onChange={e => setCardExp(e.target.value)} placeholder="MM/YY" maxLength={5}
                className="px-3 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-lg outline-none focus:border-sky-400" />
              <input value={cardCvv} onChange={e => setCardCvv(e.target.value)} placeholder="CVV" maxLength={3} type="password"
                className="px-3 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-lg outline-none focus:border-sky-400" />
            </div>
          </div>
        )}
        {payMethod === 'UPI' && (
          <input placeholder="yourname@upi"
            className="w-full px-3 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-lg outline-none focus:border-sky-400" />
        )}
        {payMethod === 'Net Banking' && (
          <select className="w-full px-3 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-lg outline-none">
            {['State Bank of India','HDFC Bank','ICICI Bank','Axis Bank'].map(b => <option key={b}>{b}</option>)}
          </select>
        )}
        {payMethod === 'COD' && (
          <div className="bg-green-50 border border-green-200 rounded-xl px-4 py-3 text-sm text-green-700">
            Cash on Delivery selected. Pay when your order arrives.
          </div>
        )}
        <div className="mt-4">
          <input value={addr} onChange={e => setAddr(e.target.value)} placeholder="Full delivery address"
            className="w-full px-3 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-lg outline-none focus:border-sky-400" />
        </div>
        <div className="flex items-center gap-2 mt-3 text-xs text-slate-400">
          <span>🔒</span> 256-bit SSL encrypted · Secured by ShopTrust Pay
        </div>
      </div>

      <div>
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
          <div className="font-bold text-slate-800 mb-4">Order summary</div>
          <div className="space-y-2 mb-4 text-sm">
            {items.map(item => (
              <div key={item.id} className="flex justify-between text-slate-600">
                <span className="truncate mr-2">{item.product_name} ×{item.quantity}</span>
                <span>₹{(item.price * item.quantity).toLocaleString()}</span>
              </div>
            ))}
          </div>
          <div className="border-t border-slate-200 pt-3 space-y-2 text-sm">
            <div className="flex justify-between text-slate-500"><span>Delivery</span><span className="text-green-500 font-semibold">FREE</span></div>
            <div className="flex justify-between font-bold text-slate-800 text-base"><span>Total</span><span>₹{total.toLocaleString()}</span></div>
          </div>
          <button onClick={() => onOrder(payMethod)} className="mt-4 w-full py-3 bg-[#0a1628] hover:bg-[#0d2240] text-white font-bold rounded-xl text-sm transition">
            Place order →
          </button>
          <button onClick={() => setCheckout(false)} className="mt-2 w-full py-2 text-xs text-slate-400 hover:text-slate-600">← Back to cart</button>
        </div>
      </div>
    </div>
  )

  return (
    <div className="max-w-2xl mx-auto p-5">
      <h2 className="text-xl font-bold text-slate-800 mb-5">Your Cart</h2>
      {items.length === 0 ? (
        <div className="text-center py-16 text-slate-400">
          <div className="text-4xl mb-3">🛒</div>
          <div>Your cart is empty</div>
          <button onClick={() => setPage('products')} className="mt-4 px-5 py-2 bg-[#0a1628] text-white text-sm font-bold rounded-xl">Browse Products</button>
        </div>
      ) : (
        <>
          <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm mb-4">
            {items.map((item, i) => (
              <div key={item.id} className={`flex items-center gap-4 p-4 ${i < items.length - 1 ? 'border-b border-slate-100' : ''}`}>
                <div className="text-3xl">{catIcon(item.category)}</div>
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-slate-800 text-sm truncate">{item.product_name}</div>
                  <div className="text-xs text-slate-400">×{item.quantity} · ₹{item.price?.toLocaleString()} each</div>
                </div>
                <div className="font-bold text-slate-800">₹{(item.price * item.quantity).toLocaleString()}</div>
                <button onClick={() => onRemove(item.product_id || item.id)} className="text-red-400 hover:text-red-600 text-xs ml-2">✕</button>
              </div>
            ))}
          </div>
          <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm flex items-center justify-between">
            <div>
              <div className="text-sm text-slate-500">Total</div>
              <div className="text-2xl font-black text-[#0a1628]">₹{total.toLocaleString()}</div>
              <div className="text-xs text-green-500 font-semibold">FREE delivery</div>
            </div>
            <button onClick={() => setCheckout(true)} className="px-6 py-3 bg-[#0a1628] hover:bg-[#0d2240] text-white font-bold rounded-xl transition">
              Checkout →
            </button>
          </div>
        </>
      )}
    </div>
  )
}
