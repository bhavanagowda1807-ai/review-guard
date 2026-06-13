import React, {useState} from 'react'
import axios from 'axios'

export default function UploadForm(){
  const [text,setText] = useState('')
  const [result,setResult] = useState(null)

  const submit = async (e)=>{
    e.preventDefault()
    const form = new FormData()
    form.append('text', text)
    const res = await axios.post('http://localhost:8000/api/predict', form)
    setResult(res.data)
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <textarea value={text} onChange={e=>setText(e.target.value)} className="w-full p-2 bg-[#1f2937]" rows={6} />
      <div>
        <button className="px-4 py-2 bg-indigo-600 rounded">Analyze</button>
      </div>
      {result && (
        <div className="mt-4 p-4 bg-[#1f2937] rounded">
          <div>Verdict: {result.verdict}</div>
          <div>Confidence: {result.confidence}</div>
        </div>
      )}
    </form>
  )
}
