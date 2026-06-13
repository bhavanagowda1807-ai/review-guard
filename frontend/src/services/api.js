import axios from 'axios'

const getApiUrl = () => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }
  // Browser: use relative URL to backend on same host
  return window.location.origin.replace(':3000', ':8000')
}

const api = axios.create({
  baseURL: getApiUrl(),
  withCredentials: false,
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('fake_review_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ── Auth ──────────────────────────────────────────────────────

export async function register(username, password, role = 'User') {
  const res = await api.post('/auth/register', { username, password, role })
  return res.data
}

export async function login(username, password) {
  const form = new URLSearchParams()
  form.append('username', username)
  form.append('password', password)
  const res = await api.post('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  })
  localStorage.setItem('fake_review_token', res.data.access_token)
  return res.data
}

export async function getMe() {
  const res = await api.get('/auth/me')
  return res.data
}

export function logout() {
  localStorage.removeItem('fake_review_token')
}

// ── Inference ─────────────────────────────────────────────────

export async function predictReview(formData) {
  const res = await api.post('/api/predict', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return res.data
}

export async function predictReviewAsync(formData) {
  const res = await api.post('/api/predict/async', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return res.data
}

export async function getPredictionTask(taskId) {
  const res = await api.get(`/api/predict/tasks/${taskId}`)
  return res.data
}

// ── Reviews ───────────────────────────────────────────────────

export async function listReviews(limit = 10) {
  const res = await api.get(`/api/reviews?limit=${limit}`)
  return res.data
}

export async function listFlaggedReviews(limit = 50) {
  const res = await api.get(`/api/reviews/flagged?limit=${limit}`)
  return res.data
}

export async function deleteReview(reviewId) {
  const res = await api.delete(`/api/reviews/${reviewId}`)
  return res.data
}

export async function flagReview(reviewId, reason) {
  const form = new URLSearchParams()
  if (reason) form.append('reason', reason)
  const res = await api.post(`/api/reviews/${reviewId}/flag`, form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  })
  return res.data
}

export async function unflagReview(reviewId) {
  const res = await api.post(`/api/reviews/${reviewId}/unflag`)
  return res.data
}

// ── Explainability ────────────────────────────────────────────

export async function explainText(text) {
  const form = new FormData()
  form.append('text', text)
  const res = await api.post('/api/explain/text', form)
  return res.data
}

// explainImage removed — text-only mode

export async function explainMetadata(metadata) {
  const form = new FormData()
  Object.entries(metadata).forEach(([key, value]) => form.append(key, value))
  const res = await api.post('/api/explain/metadata', form)
  return res.data
}

export async function explainAttention(text_score, meta_score) {
  const form = new FormData()
  if (text_score != null) form.append('text_score', text_score)
  if (meta_score != null) form.append('meta_score', meta_score)
  const res = await api.post('/api/explain/attention', form)
  return res.data
}

// ── Misc ──────────────────────────────────────────────────────

export async function getHealth() {
  const res = await api.get('/api/health')
  return res.data
}

export async function getModelCard() {
  const res = await api.get('/api/model-card')
  return res.data
}

export async function listAuditLogs(page = 1, pageSize = 50) {
  const res = await api.get(`/api/audit?page=${page}&page_size=${pageSize}`)
  return res.data
}

export default api

// ── Shop ──────────────────────────────────────────────────────

export async function shopLogin(username, password, role = 'User') {
  const res = await api.post('/api/shop/login', { username, password, role })
  return res.data
}

export async function shopRegister(data) {
  const res = await api.post('/api/shop/register', data)
  return res.data
}

export async function shopLogout() {
  const res = await api.post('/api/shop/logout', {})
  return res.data
}

export async function getShopProducts(category) {
  const params = category ? `?category=${category}` : ''
  const res = await api.get(`/api/shop/products${params}`)
  return res.data
}

export async function getProductReviews(productId) {
  const res = await api.get(`/api/shop/products/${productId}/reviews`)
  return res.data
}

export async function getCart() {
  const res = await api.get('/api/shop/cart')
  return res.data
}

export async function addToCart(productId, qty = 1) {
  const res = await api.post('/api/shop/cart/add', { product_id: productId, qty })
  return res.data
}

export async function removeFromCart(cartId) {
  const res = await api.post('/api/shop/cart/remove', { cart_id: cartId })
  return res.data
}

export async function placeOrder(paymentMethod) {
  const res = await api.post('/api/shop/orders/place', { payment_method: paymentMethod })
  return res.data
}

export async function getOrders() {
  const res = await api.get('/api/shop/orders')
  return res.data
}

export async function getOrderItems(orderId) {
  const res = await api.get(`/api/shop/orders/${orderId}/items`)
  return res.data
}

export async function markOrderDelivered(orderId) {
  const res = await api.post(`/api/shop/orders/${orderId}/deliver`, {})
  return res.data
}

export async function submitShopReview(data) {
  const res = await api.post('/api/shop/reviews/submit', data)
  return res.data
}

export async function getRankings(category) {
  const params = category && category !== 'All' ? `?category=${category}` : ''
  const res = await api.get(`/api/shop/rankings${params}`)
  return res.data
}

export async function submitFeedback(data) {
  const res = await api.post('/api/shop/feedback', data)
  return res.data
}

export async function getOwnerStats() {
  const res = await api.get('/api/shop/owner/stats')
  return res.data
}

export async function getOwnerProducts() {
  const res = await api.get('/api/shop/owner/products')
  return res.data
}

export async function addOwnerProduct(data) {
  const res = await api.post('/api/shop/owner/products/add', data)
  return res.data
}

export async function deleteOwnerProduct(productId) {
  const res = await api.delete(`/api/shop/products/${productId}`)
  return res.data
}

export async function getOwnerOrders() {
  const res = await api.get('/api/shop/owner/orders')
  return res.data
}

export async function getOwnerReviews() {
  const res = await api.get('/api/shop/owner/reviews')
  return res.data
}

export async function uploadCsvBatch(file) {
  const formData = new FormData()
  formData.append('csv_file', file)
  const res = await api.post('/api/shop/upload/reviews', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return res.data
}

export async function listUploadBatches() {
  const res = await api.get('/api/shop/upload/batches')
  return res.data
}
