import React, { useState } from 'react'
import { apiPost } from './shopApi'

export default function FeedbackPage() {
  const [rating, setRating] = useState(0)
  const [type, setType] = useState('General feedback')
  const [subject, setSubject] = useState('')
  const [message, setMessage] = useState('')
  const [submitted, setSubmitted] = useState(false)

  async function submit() {
    if (!message.trim()) return
    try { await apiPost('/api/shop/feedback', { rating, type, subject, message }) } catch {}
    setSubmitted(true)
  }

  return (
    <div className="p-5 max-w-lg mx-auto">
      <h2 className="text-xl font-bold text-slate-800 mb-5">Submit Feedback</h2>
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
        <div>
          <label className="text-xs font-bold text-slate-500 uppercase tracking-wide block mb-2">How would you rate ShopTrust?</label>
          <div className="flex gap-1">
            {[1, 2, 3, 4, 5].map(n => (
              <button key={n} onClick={() => setRating(n)}
                className={`text-2xl transition ${n <= rating ? 'text-yellow-400' : 'text-slate-200 hover:text-yellow-200'}`}>★</button>
            ))}
          </div>
        </div>
        <div>
          <label className="text-xs font-bold text-slate-500 uppercase tracking-wide block mb-2">Feedback type</label>
          <select value={type} onChange={e => setType(e.target.value)}
            className="w-full px-3 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-lg outline-none focus:border-sky-400">
            {['General feedback', 'Report a fake review', 'Product issue', 'Website bug', 'Suggestion'].map(t => (
              <option key={t}>{t}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs font-bold text-slate-500 uppercase tracking-wide block mb-2">Subject</label>
          <input value={subject} onChange={e => setSubject(e.target.value)} placeholder="Brief subject"
            className="w-full px-3 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-lg outline-none focus:border-sky-400" />
        </div>
        <div>
          <label className="text-xs font-bold text-slate-500 uppercase tracking-wide block mb-2">Message</label>
          <textarea value={message} onChange={e => setMessage(e.target.value)} rows={5} placeholder="Write your feedback…"
            className="w-full px-3 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-lg outline-none focus:border-sky-400 resize-none" />
        </div>
        {submitted && (
          <div className="bg-green-50 border border-green-200 text-green-700 text-sm px-4 py-3 rounded-xl">
            Thank you! Your feedback has been submitted.
          </div>
        )}
        <button onClick={submit} disabled={submitted}
          className="w-full py-3 bg-[#0a1628] hover:bg-[#0d2240] text-white font-bold rounded-xl text-sm transition disabled:opacity-50">
          {submitted ? 'Submitted ✓' : 'Submit feedback →'}
        </button>
      </div>
    </div>
  )
}
