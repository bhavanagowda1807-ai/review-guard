export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const CATEGORIES = ['All', 'Electronics', 'Clothing', 'Home & Kitchen', 'Books', 'Beauty', 'Sports']
export const CATEGORY_ICON = { Electronics: '📱', Clothing: '👕', Books: '📚', 'Home & Kitchen': '🏠', Sports: '⚽', Beauty: '💄', Other: '📦' }
export const catIcon = c => CATEGORY_ICON[c] || '📦'

export function getToken() { return localStorage.getItem('fake_review_token') }
export function authHeaders() {
  const t = getToken()
  return t ? { Authorization: `Bearer ${t}` } : {}
}
export async function apiFetch(path, opts = {}) {
  const res = await fetch(`${API_BASE}${path}`, { headers: { ...authHeaders(), ...opts.headers }, ...opts })
  return res.ok ? res.json() : Promise.reject(await res.json().catch(() => ({})))
}
export async function apiPost(path, data) {
  return apiFetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
}
