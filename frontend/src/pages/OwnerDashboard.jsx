import React, { useEffect, useState, useRef } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const CATEGORIES = ['Electronics', 'Clothing', 'Home & Kitchen', 'Books', 'Beauty', 'Sports', 'Toys', 'Grocery']

function getToken() { return localStorage.getItem('fake_review_token') }
function authHeaders() { const t = getToken(); return t ? { Authorization: `Bearer ${t}` } : {} }
async function apiFetch(path, opts = {}) {
  const res = await fetch(`${API_BASE}${path}`, { headers: { ...authHeaders(), ...opts.headers }, ...opts })
  if (!res.ok) throw await res.json().catch(() => ({}))
  return res.json()
}

// ── Shared UI ─────────────────────────────────────────────────

function KPI({ label, value, color, icon, sub }) {
  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
      <div className="flex items-start justify-between mb-1">
        <div className={`text-3xl font-black ${color || 'text-slate-800'}`}>{value ?? '—'}</div>
        {icon && <span className="text-2xl">{icon}</span>}
      </div>
      <div className="text-xs text-slate-400 font-semibold uppercase tracking-wide">{label}</div>
      {sub && <div className="text-xs text-slate-400 mt-0.5">{sub}</div>}
    </div>
  )
}

function Badge({ v }) {
  if (v === 'fake') return <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-red-100 text-red-500">fake</span>
  if (v === 'genuine') return <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-green-100 text-green-600">genuine</span>
  return <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-400">{v || 'pending'}</span>
}

function Toast({ msg, type = 'success', onClose }) {
  useEffect(() => { if (msg) { const t = setTimeout(onClose, 3500); return () => clearTimeout(t) } }, [msg])
  if (!msg) return null
  const colors = type === 'error' ? 'bg-red-600' : 'bg-emerald-600'
  return (
    <div className={`fixed bottom-5 right-5 z-50 ${colors} text-white text-sm font-semibold px-5 py-3 rounded-xl shadow-xl flex items-center gap-3`}>
      <span>{msg}</span>
      <button onClick={onClose} className="opacity-60 hover:opacity-100 text-lg leading-none">✕</button>
    </div>
  )
}

// ── Nav ───────────────────────────────────────────────────────

function OwnerNav({ active, setActive }) {
  const items = [
    { id: 'overview',     icon: '📊', label: 'Overview' },
    { id: 'products',     icon: '📦', label: 'My Products' },
    { id: 'add-product',  icon: '➕', label: 'Add Product' },
    { id: 'reviews',      icon: '💬', label: 'All Reviews' },
    { id: 'orders',       icon: '🚚', label: 'Manage Orders' },
  ]
  return (
    <div className="w-52 shrink-0">
      <div className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3 px-3">Seller Menu</div>
      {items.map(it => (
        <button key={it.id} onClick={() => setActive(it.id)}
          className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-semibold transition mb-0.5 text-left
            ${active === it.id ? 'bg-[#0a1628] text-white' : 'text-slate-600 hover:bg-slate-100'}`}>
          <span>{it.icon}</span>{it.label}
        </button>
      ))}
    </div>
  )
}

// ── Overview ──────────────────────────────────────────────────

function OverviewSection({ stats, setActive }) {
  const trustScore = stats?.total > 0 ? Math.round(((stats.genuine || 0) / stats.total) * 100) : 0
  return (
    <div>
      <h2 className="text-xl font-bold text-slate-800 mb-5">Dashboard Overview</h2>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <KPI label="Active Products"  value={stats?.products}      icon="📦" />
        <KPI label="Total Reviews"    value={stats?.total}         icon="💬" />
        <KPI label="Genuine"          value={stats?.genuine}       icon="✅" color="text-green-500" />
        <KPI label="Flagged Fake"     value={stats?.fake}          icon="🚨" color="text-red-500" />
        <KPI label="Total Orders"     value={stats?.total_orders}  icon="🛒" />
        <KPI label="Pending Orders"   value={stats?.pending_orders} icon="⏳" color="text-yellow-500" />
      </div>

      <div className="bg-gradient-to-br from-[#0a1628] to-[#1e3f70] rounded-2xl p-6 text-white mb-6">
        <div className="text-lg font-bold mb-1">Trust Score</div>
        <div className="text-5xl font-black text-sky-300">{trustScore}<span className="text-2xl font-normal text-white/60">/100</span></div>
        <div className="text-sm text-white/50 mt-1">Based on genuine vs total review ratio</div>
        <div className="mt-4 h-2 bg-white/15 rounded-full overflow-hidden">
          <div className="h-full bg-sky-400 rounded-full transition-all" style={{ width: `${trustScore}%` }} />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {[
          { id: 'add-product', icon: '➕', label: 'Add Product' },
          { id: 'products',    icon: '📦', label: 'Manage Products' },
          { id: 'orders',      icon: '🚚', label: 'Manage Orders' },
        ].map(it => (
          <button key={it.id} onClick={() => setActive(it.id)}
            className="bg-white border border-slate-200 rounded-2xl p-5 text-center shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all">
            <div className="text-3xl mb-2">{it.icon}</div>
            <div className="text-sm font-bold text-slate-800">{it.label}</div>
          </button>
        ))}
      </div>
    </div>
  )
}

// ── Products ──────────────────────────────────────────────────

function EditModal({ product, onSave, onClose }) {
  const [form, setForm] = useState({
    name: product.name || '', category: product.category || '',
    price: product.price || '', description: product.description || '',
    keywords: product.keywords || '',
  })
  const [saving, setSaving] = useState(false)
  const f = (k, v) => setForm(p => ({ ...p, [k]: v }))

  async function save() {
    setSaving(true)
    const fd = new FormData()
    Object.entries(form).forEach(([k, v]) => v !== '' && fd.append(k, v))
    try {
      const res = await fetch(`${API_BASE}/api/shop/products/${product.id}`, {
        method: 'PATCH', headers: authHeaders(), body: fd,
      })
      if (res.ok) { onSave(); onClose() }
    } catch {}
    setSaving(false)
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-lg font-bold text-slate-800">Edit Product</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-xl">✕</button>
        </div>
        <div className="grid grid-cols-2 gap-3 mb-3">
          {[['name','Product Name'], ['category','Category'], ['price','Price (₹)'], ['keywords','Keywords']].map(([k, lbl]) => (
            k === 'category' ? (
              <div key={k}>
                <label className="text-xs font-bold text-slate-500 uppercase block mb-1">{lbl}</label>
                <select value={form[k]} onChange={e => f(k, e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl outline-none focus:border-sky-400">
                  <option value="">Choose…</option>
                  {CATEGORIES.map(c => <option key={c}>{c}</option>)}
                </select>
              </div>
            ) : (
              <div key={k}>
                <label className="text-xs font-bold text-slate-500 uppercase block mb-1">{lbl}</label>
                <input value={form[k]} onChange={e => f(k, e.target.value)}
                  type={k === 'price' ? 'number' : 'text'}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl outline-none focus:border-sky-400" />
              </div>
            )
          ))}
        </div>
        <div className="mb-4">
          <label className="text-xs font-bold text-slate-500 uppercase block mb-1">Description</label>
          <textarea value={form.description} onChange={e => f('description', e.target.value)} rows={3}
            className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl outline-none focus:border-sky-400 resize-none" />
        </div>
        <div className="flex gap-3 justify-end">
          <button onClick={onClose} className="px-4 py-2 border border-slate-200 text-slate-600 text-sm font-semibold rounded-xl hover:bg-slate-50">Cancel</button>
          <button onClick={save} disabled={saving}
            className="px-5 py-2 bg-[#0a1628] text-white text-sm font-bold rounded-xl hover:bg-[#0d2240] disabled:opacity-50">
            {saving ? 'Saving…' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  )
}

function ProductsSection({ products, onRefresh, onToast }) {
  const [editing, setEditing] = useState(null)
  const [confirmDelete, setConfirmDelete] = useState(null)

  async function toggleActive(id) {
    try {
      const res = await fetch(`${API_BASE}/api/shop/products/${id}/toggle`, { method: 'PATCH', headers: authHeaders() })
      const d = await res.json()
      onToast(d.detail)
      onRefresh()
    } catch { onToast('Failed to update', 'error') }
  }

  async function deleteProduct(id) {
    try {
      await fetch(`${API_BASE}/api/shop/products/${id}`, { method: 'DELETE', headers: authHeaders() })
      onToast('Product removed')
      onRefresh()
    } catch { onToast('Failed to remove', 'error') }
    setConfirmDelete(null)
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-xl font-bold text-slate-800">My Product Listings</h2>
        <span className="text-xs text-slate-400">{products.length} products</span>
      </div>

      <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                {['#','Product','Category','Price','Reviews','Fake %','Status','Actions'].map(h => (
                  <th key={h} className="text-left px-4 py-3 text-xs font-bold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {products.length === 0 ? (
                <tr><td colSpan={8} className="text-center py-12 text-slate-400">No products yet. Add your first product!</td></tr>
              ) : products.map((p, i) => {
                const fakePct = p.review_count > 0 ? ((p.fake_count / p.review_count) * 100).toFixed(0) : null
                return (
                  <tr key={p.id} className="border-b border-slate-100 hover:bg-slate-50 transition">
                    <td className="px-4 py-3 text-slate-400">{i + 1}</td>
                    <td className="px-4 py-3">
                      <div className="font-semibold text-slate-800">{p.name}</div>
                      {p.description && <div className="text-xs text-slate-400 truncate max-w-[160px]">{p.description}</div>}
                    </td>
                    <td className="px-4 py-3 text-slate-500">{p.category}</td>
                    <td className="px-4 py-3 font-bold text-[#0a1628]">₹{Number(p.price).toLocaleString()}</td>
                    <td className="px-4 py-3 text-slate-600">{p.review_count}</td>
                    <td className="px-4 py-3">
                      {fakePct !== null
                        ? <span className={`font-bold ${Number(fakePct) > 30 ? 'text-red-500' : 'text-green-500'}`}>{fakePct}%</span>
                        : <span className="text-slate-300">—</span>}
                    </td>
                    <td className="px-4 py-3">
                      <button onClick={() => toggleActive(p.id)}
                        className={`px-2 py-0.5 rounded-full text-xs font-bold cursor-pointer transition
                          ${p.is_active ? 'bg-green-100 text-green-600 hover:bg-red-100 hover:text-red-500' : 'bg-slate-100 text-slate-400 hover:bg-green-100 hover:text-green-600'}`}>
                        {p.is_active ? 'Active' : 'Inactive'}
                      </button>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <button onClick={() => setEditing(p)} className="text-sky-500 hover:text-sky-700 text-xs font-semibold transition">Edit</button>
                        <button onClick={() => setConfirmDelete(p)} className="text-red-400 hover:text-red-600 text-xs font-semibold transition">Remove</button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Edit Modal */}
      {editing && <EditModal product={editing} onSave={onRefresh} onClose={() => setEditing(null)} />}

      {/* Confirm Delete */}
      {confirmDelete && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl p-6 max-w-sm w-full">
            <h3 className="text-lg font-bold text-slate-800 mb-2">Remove Product?</h3>
            <p className="text-sm text-slate-500 mb-5">
              <strong>{confirmDelete.name}</strong> will be deactivated and hidden from the shop.
            </p>
            <div className="flex gap-3">
              <button onClick={() => setConfirmDelete(null)} className="flex-1 px-4 py-2 border border-slate-200 text-slate-600 text-sm font-semibold rounded-xl">Cancel</button>
              <button onClick={() => deleteProduct(confirmDelete.id)} className="flex-1 px-4 py-2 bg-red-500 hover:bg-red-600 text-white text-sm font-bold rounded-xl">Remove</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ── Add Product ───────────────────────────────────────────────

function AddProductSection({ onAdded, onToast }) {
  const [form, setForm] = useState({ name: '', category: '', price: '', keywords: '', description: '' })
  const [imageFile, setImageFile] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)
  const f = (k, v) => setForm(p => ({ ...p, [k]: v }))

  async function submit() {
    if (!form.name || !form.price || !form.category) { setErr('Name, category and price are required.'); return }
    setErr(''); setLoading(true)
    try {
      const fd = new FormData()
      Object.entries(form).forEach(([k, v]) => fd.append(k, v))
      if (imageFile) fd.append('image', imageFile)
      const res = await fetch(`${API_BASE}/api/shop/products`, { method: 'POST', headers: authHeaders(), body: fd })
      if (!res.ok) { const e = await res.json().catch(() => ({})); setErr(e.detail || 'Failed'); setLoading(false); return }
      setForm({ name: '', category: '', price: '', keywords: '', description: '' })
      setImageFile(null); setImagePreview(null)
      onAdded(); onToast('Product added successfully!')
    } catch { setErr('Failed to add product') }
    setLoading(false)
  }

  return (
    <div>
      <h2 className="text-xl font-bold text-slate-800 mb-5">Add New Product</h2>
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm max-w-2xl">
        <div className="grid grid-cols-2 gap-4 mb-4">
          {[['name','Product name *','text','e.g. Wireless Headphones'], ['price','Price (₹) *','number','1999'], ['keywords','Keywords','text','tag1, tag2']].map(([k, lbl, type, ph]) => (
            <div key={k}>
              <label className="text-xs font-bold text-slate-500 uppercase tracking-wide block mb-1.5">{lbl}</label>
              <input type={type} value={form[k]} onChange={e => f(k, e.target.value)} placeholder={ph}
                className="w-full px-3 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl outline-none focus:border-sky-400" />
            </div>
          ))}
          <div>
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wide block mb-1.5">Category *</label>
            <select value={form.category} onChange={e => f('category', e.target.value)}
              className="w-full px-3 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl outline-none focus:border-sky-400">
              <option value="">Choose category</option>
              {CATEGORIES.map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
        </div>

        <div className="mb-4">
          <label className="text-xs font-bold text-slate-500 uppercase tracking-wide block mb-1.5">Product image (optional)</label>
          <div className="flex items-center gap-4">
            <label className="cursor-pointer flex items-center gap-2 px-4 py-2.5 bg-slate-100 border-2 border-dashed border-slate-300 hover:border-sky-400 rounded-xl text-sm text-slate-600 font-semibold transition">
              📷 {imageFile ? imageFile.name : 'Choose image'}
              <input type="file" accept="image/*" className="hidden" onChange={e => {
                const file = e.target.files[0]; if (!file) return
                setImageFile(file)
                const r = new FileReader(); r.onload = ev => setImagePreview(ev.target.result); r.readAsDataURL(file)
              }} />
            </label>
            {imagePreview && (
              <div className="relative">
                <img src={imagePreview} alt="preview" className="w-16 h-16 object-cover rounded-xl border border-slate-200" />
                <button onClick={() => { setImageFile(null); setImagePreview(null) }}
                  className="absolute -top-1.5 -right-1.5 w-4 h-4 bg-red-400 text-white rounded-full text-[9px] font-black flex items-center justify-center">✕</button>
              </div>
            )}
          </div>
        </div>

        <div className="mb-5">
          <label className="text-xs font-bold text-slate-500 uppercase tracking-wide block mb-1.5">Description</label>
          <textarea value={form.description} onChange={e => f('description', e.target.value)} rows={4} placeholder="Describe your product…"
            className="w-full px-3 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl outline-none focus:border-sky-400 resize-none" />
        </div>

        {err && <div className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-xl px-4 py-3 mb-4">{err}</div>}

        <div className="flex gap-3">
          <button onClick={() => { setForm({ name:'',category:'',price:'',keywords:'',description:'' }); setImageFile(null); setImagePreview(null) }}
            className="px-5 py-2.5 border border-slate-200 text-slate-600 font-semibold text-sm rounded-xl hover:bg-slate-50 transition">Clear</button>
          <button onClick={submit} disabled={loading}
            className="px-6 py-2.5 bg-[#0a1628] hover:bg-[#0d2240] text-white font-bold text-sm rounded-xl transition disabled:opacity-50">
            {loading ? 'Adding…' : 'Add product →'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── All Reviews (read-only) ───────────────────────────────────

function AllReviewsSection() {
  const [reviews, setReviews] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')
  const [search, setSearch] = useState('')

  useEffect(() => { load() }, [filter])

  async function load() {
    setLoading(true)
    try {
      const qs = filter ? `?verdict=${filter}` : ''
      setReviews(await apiFetch(`/api/shop/owner/reviews${qs}`))
    } catch { setReviews([]) }
    setLoading(false)
  }

  const visible = reviews.filter(r =>
    !search || r.text?.toLowerCase().includes(search.toLowerCase()) ||
    r.username?.toLowerCase().includes(search.toLowerCase()) ||
    r.product_name?.toLowerCase().includes(search.toLowerCase())
  )

  const total = reviews.length
  const fakeCount = reviews.filter(r => r.verdict === 'fake').length
  const genuineCount = reviews.filter(r => r.verdict === 'genuine').length

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-xl font-bold text-slate-800">All Reviews</h2>
        <span className="text-xs text-slate-400 bg-slate-100 px-3 py-1 rounded-full">👁 View only — deletion not permitted</span>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-5">
        <KPI label="Total" value={total} icon="💬" />
        <KPI label="Genuine" value={genuineCount} icon="✅" color="text-green-500" />
        <KPI label="Fake" value={fakeCount} icon="🚨" color="text-red-500" />
      </div>

      <div className="flex flex-wrap gap-3 mb-4">
        <div className="flex gap-1 bg-slate-100 p-1 rounded-xl">
          {[['', 'All'], ['genuine', 'Genuine'], ['fake', 'Fake'], ['pending', 'Pending']].map(([v, lbl]) => (
            <button key={v} onClick={() => setFilter(v)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${filter === v ? 'bg-white shadow text-slate-800' : 'text-slate-500 hover:text-slate-700'}`}>
              {lbl}
            </button>
          ))}
        </div>
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search text, reviewer, product…"
          className="px-3 py-2 text-sm border border-slate-200 rounded-xl outline-none focus:border-sky-400 w-56" />
        <button onClick={load} className="px-3 py-2 bg-slate-800 text-white text-xs font-bold rounded-xl hover:bg-slate-700">↻</button>
      </div>

      <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                {['#','Product','Reviewer','Rating','Review','Verdict','Confidence','Date'].map(h => (
                  <th key={h} className="text-left px-4 py-3 text-xs font-bold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={8} className="text-center py-10 text-slate-400">Loading…</td></tr>
              ) : visible.length === 0 ? (
                <tr><td colSpan={8} className="text-center py-10 text-slate-400">No reviews found</td></tr>
              ) : visible.map((r, i) => (
                <tr key={r.id} className="border-b border-slate-100 hover:bg-slate-50 transition">
                  <td className="px-4 py-3 text-slate-400">{i + 1}</td>
                  <td className="px-4 py-3 text-slate-500 max-w-[120px] truncate">{r.product_name || '—'}</td>
                  <td className="px-4 py-3 font-medium text-slate-700">{r.username || '—'}</td>
                  <td className="px-4 py-3 text-yellow-400">{'★'.repeat(r.rating || 0)}<span className="text-slate-300">{'★'.repeat(5 - (r.rating || 0))}</span></td>
                  <td className="px-4 py-3 text-slate-500 max-w-[200px]">
                    <span className="line-clamp-2">{r.text || '—'}</span>
                  </td>
                  <td className="px-4 py-3"><Badge v={r.verdict} /></td>
                  <td className="px-4 py-3 text-slate-600 font-mono text-xs">
                    {r.confidence != null ? `${(r.confidence * 100).toFixed(1)}%` : '—'}
                  </td>
                  <td className="px-4 py-3 text-slate-400 text-xs whitespace-nowrap">
                    {r.created_at ? new Date(r.created_at).toLocaleDateString() : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

// ── Manage Orders ─────────────────────────────────────────────

function ManageOrdersSection({ onToast }) {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  useEffect(() => { load() }, [])

  async function load() {
    setLoading(true)
    try { setOrders(await apiFetch('/api/shop/owner/orders')) } catch { setOrders([]) }
    setLoading(false)
  }

  async function advanceStatus(id, currentStatus) {
    try {
      await apiFetch(`/api/shop/orders/${id}/advance`, { method: 'POST' })
      const labels = { pending: 'Processing', processing: 'Shipped', shipped: 'Delivered' }
      onToast(`Order moved to ${labels[currentStatus?.toLowerCase()] || 'next status'}`)
      load()
    } catch (e) { onToast(e?.message || 'Failed to update order', 'error') }
  }

  const filtered = orders
    .filter(o => !search ||
      (o.buyer_username || '').toLowerCase().includes(search.toLowerCase()) ||
      String(o.id).includes(search))
    .filter(o => !statusFilter || o.status?.toLowerCase() === statusFilter.toLowerCase())

  const byStatus = (s) => orders.filter(o => (o.status || 'pending').toLowerCase() === s).length

  return (
    <div>
      <h2 className="text-xl font-bold text-slate-800 mb-1">Manage Orders</h2>
      <p className="text-sm text-slate-400 mb-5">Advance orders through the pipeline — customers can review once Delivered</p>

      <div className="grid grid-cols-5 gap-3 mb-5">
        <KPI label="Total"      value={orders.length}           icon="🛒" />
        <KPI label="Pending"    value={byStatus('pending')}     icon="⏳" color="text-yellow-500" />
        <KPI label="Processing" value={byStatus('processing')}  icon="⚙️" color="text-blue-500" />
        <KPI label="Shipped"    value={byStatus('shipped')}     icon="📦" color="text-purple-500" />
        <KPI label="Delivered"  value={byStatus('delivered')}   icon="✅" color="text-green-500" />
      </div>

      <div className="flex flex-wrap gap-3 mb-4">
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search by customer or order ID…"
          className="px-3 py-2 text-sm border border-slate-200 rounded-xl outline-none focus:border-sky-400 w-56" />
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
          className="px-3 py-2 text-sm border border-slate-200 rounded-xl outline-none">
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="processing">Processing</option>
          <option value="shipped">Shipped</option>
          <option value="delivered">Delivered</option>
          <option value="cancelled">Cancelled</option>
        </select>
        <button onClick={load} className="px-3 py-2 bg-slate-800 text-white text-xs font-bold rounded-xl hover:bg-slate-700">↻ Refresh</button>
        <span className="self-center text-xs text-slate-400">{filtered.length} orders</span>
      </div>

      <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                {['#','Order ID','Customer','Items','Total','Payment','Date','Status','Action'].map(h => (
                  <th key={h} className="text-left px-4 py-3 text-xs font-bold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={9} className="text-center py-10 text-slate-400">Loading…</td></tr>
              ) : filtered.length === 0 ? (
                <tr><td colSpan={9} className="text-center py-10 text-slate-400">No orders found</td></tr>
              ) : filtered.map((o, i) => (
                <tr key={o.id} className="border-b border-slate-100 hover:bg-slate-50 transition">
                  <td className="px-4 py-3 text-slate-400">{i + 1}</td>
                  <td className="px-4 py-3 font-mono font-bold text-slate-700">#{String(o.id).padStart(6, '0')}</td>
                  <td className="px-4 py-3 font-medium text-slate-700">{o.buyer_username || '—'}</td>
                  <td className="px-4 py-3 text-slate-500 text-xs max-w-[140px]">
                    {o.items?.length > 0
                      ? o.items.map((it, j) => <div key={j}>{it.product_name} ×{it.quantity}</div>)
                      : '—'}
                  </td>
                  <td className="px-4 py-3 font-bold text-[#0a1628]">₹{Number(o.total_amount || 0).toLocaleString()}</td>
                  <td className="px-4 py-3 text-slate-500 capitalize">{o.payment_method || 'card'}</td>
                  <td className="px-4 py-3 text-slate-400 text-xs">{o.ordered_at ? new Date(o.ordered_at).toLocaleDateString() : '—'}</td>
                  <td className="px-4 py-3">
                    {(() => {
                      const s = (o.status || 'pending').toLowerCase()
                      const cfg = {
                        pending:    { cls: 'bg-yellow-100 text-yellow-700', label: '⏳ Pending' },
                        processing: { cls: 'bg-blue-100 text-blue-700',   label: '⚙️ Processing' },
                        shipped:    { cls: 'bg-purple-100 text-purple-700', label: '📦 Shipped' },
                        delivered:  { cls: 'bg-green-100 text-green-700',  label: '✅ Delivered' },
                        cancelled:  { cls: 'bg-red-100 text-red-600',      label: '✖ Cancelled' },
                        completed:  { cls: 'bg-green-100 text-green-700',  label: '✅ Delivered' },
                      }
                      const { cls, label } = cfg[s] || cfg.pending
                      return <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${cls}`}>{label}</span>
                    })()}
                  </td>
                  <td className="px-4 py-3">
                    {(() => {
                      const s = (o.status || 'pending').toLowerCase()
                      const nextLabel = { pending: '▶ Process', processing: '📦 Ship', shipped: '✅ Deliver' }
                      if (!nextLabel[s]) return null
                      const btnCls = s === 'shipped'
                        ? 'bg-green-500 hover:bg-green-600'
                        : s === 'processing'
                          ? 'bg-purple-500 hover:bg-purple-600'
                          : 'bg-blue-500 hover:bg-blue-600'
                      return (
                        <button onClick={() => advanceStatus(o.id, s)}
                          className={`px-3 py-1.5 ${btnCls} text-white text-xs font-bold rounded-lg transition`}>
                          {nextLabel[s]}
                        </button>
                      )
                    })()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

// ── Root ──────────────────────────────────────────────────────

export default function OwnerDashboard({ user: propUser, navigate }) {
  const [activeSection, setActiveSection] = useState('overview')
  const [products, setProducts] = useState([])
  const [stats, setStats] = useState(null)
  const [toast, setToast] = useState({ msg: '', type: 'success' })

  useEffect(() => { fetchProducts(); fetchStats() }, [])

  async function fetchProducts() {
    try { setProducts(await apiFetch('/api/shop/owner/products')) }
    catch { try { setProducts(await apiFetch('/api/shop/products')) } catch { setProducts([]) } }
  }

  async function fetchStats() {
    try { setStats(await apiFetch('/api/shop/owner/stats')) }
    catch { try { setStats(await apiFetch('/api/shop/stats/reviews')) } catch {} }
  }

  function showToast(msg, type = 'success') { setToast({ msg, type }) }

  const username = propUser?.username || propUser?.full_name || 'Seller'

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <nav className="sticky top-0 z-40 bg-[#0a1628] border-b border-white/10 shadow-lg">
        <div className="max-w-7xl mx-auto px-5 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-white text-lg">
            <span className="w-2 h-2 rounded-full bg-sky-400 inline-block" />
            ShopTrust <span className="text-white/40 text-xs font-normal ml-1">Seller</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-white/10 border border-white/20 rounded-full">
              <span className="w-6 h-6 rounded-full bg-sky-400 text-[#0a1628] text-[10px] font-black flex items-center justify-center">{username[0].toUpperCase()}</span>
              <span className="text-sm text-white/90 font-semibold">{username}</span>
              <span className="text-xs text-sky-300 font-bold bg-sky-400/20 px-1.5 py-0.5 rounded-md">Owner</span>
            </div>
            {navigate && (
              <button onClick={() => navigate('/shop')} className="text-white/60 hover:text-white text-sm transition">← Shop</button>
            )}
            <button onClick={() => { localStorage.removeItem('fake_review_token'); if (navigate) navigate('/') }}
              className="px-3 py-1.5 bg-red-700/80 hover:bg-red-600 text-white text-xs font-bold rounded-md transition">Sign out</button>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-5 py-6 flex gap-6">
        <OwnerNav active={activeSection} setActive={setActiveSection} />
        <div className="flex-1 min-w-0">
          {activeSection === 'overview'    && <OverviewSection stats={stats} setActive={setActiveSection} />}
          {activeSection === 'products'    && <ProductsSection products={products} onRefresh={fetchProducts} onToast={showToast} />}
          {activeSection === 'add-product' && <AddProductSection onAdded={() => { fetchProducts(); fetchStats() }} onToast={showToast} />}
          {activeSection === 'reviews'     && <AllReviewsSection />}
          {activeSection === 'orders'      && <ManageOrdersSection onToast={showToast} />}
        </div>
      </div>

      <Toast msg={toast.msg} type={toast.type} onClose={() => setToast({ msg: '', type: 'success' })} />
    </div>
  )
}
