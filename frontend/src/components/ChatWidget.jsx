import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { errorMessage } from '../api/client'
import FeeTable from './FeeTable'

export default function ChatWidget() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Assalam-o-Alaikum! I am UniAssist. Ask me about fees, programs or admissions — in English, Urdu or Roman Urdu.', suggestions: ['BS AI ki fee kitni hai?', 'What is the fee for BS Computer Science?', 'بی ایس انگلش کی فیس کتنی ہے؟'] },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState(() => localStorage.getItem('chat_session') || null)
  const listRef = useRef(null)

  // Scroll only the widget's own message list (scrollIntoView dragged the
  // whole page down — same bug as the full chat page).
  useEffect(() => {
    const el = listRef.current
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  }, [messages, open, loading])

  const send = async (text) => {
    const msg = (text ?? input).trim()
    if (!msg || loading) return
    setInput('')
    setMessages((m) => [...m, { role: 'user', content: msg }])
    setLoading(true)
    try {
      const { data } = await api.post('/chat', { message: msg, session_id: sessionId })
      if (data.session_id) { setSessionId(data.session_id); localStorage.setItem('chat_session', data.session_id) }
      setMessages((m) => [...m, { role: 'assistant', content: data.answer, sources: data.sources, fee_table: data.fee_table, suggestions: data.suggestions, message_id: data.message_id }])
    } catch (err) {
      setMessages((m) => [...m, { role: 'assistant', content: errorMessage(err, 'Sorry, the chatbot is unavailable right now. Please try again.') }])
    } finally { setLoading(false) }
  }

  if (!open) {
    return (
      <button onClick={() => setOpen(true)} className="fixed bottom-5 end-5 z-50 flex items-center gap-2 rounded-full bg-navy px-4 py-3 text-white shadow-xl hover:bg-navy-light" aria-label="Open chat">
        <img src="/assets/iub-logo.jpg" alt="" className="h-7 w-7 rounded-full bg-white object-contain" />
        <span className="text-sm font-bold">Ask UniAssist</span>
      </button>
    )
  }

  return (
    <div className="fixed bottom-4 end-4 z-50 flex h-[min(560px,85vh)] w-[min(380px,calc(100vw-2rem))] flex-col overflow-hidden rounded-2xl border border-slate-200 dark:border-white/10 bg-white dark:bg-[#1B154D] shadow-2xl">
      <div className="flex items-center gap-2 bg-navy px-4 py-3 text-white">
        <img src="/assets/iub-logo.jpg" alt="" className="h-8 w-8 rounded-full bg-white object-contain" />
        <div className="flex-1 leading-tight">
          <p className="text-sm font-bold">UniAssist Chatbot</p>
          <p className="text-[11px] text-gold-light">English · اردو · Roman Urdu</p>
        </div>
        <Link to="/chat" className="text-xs underline text-white/80">Full page</Link>
        <button onClick={() => setOpen(false)} className="ms-1 text-lg" aria-label="Close">✕</button>
      </div>

      <div ref={listRef} className="chat-scroll flex-1 overflow-y-auto p-3 space-y-3">
        {messages.map((m, i) => (
          <div key={i}>
            <div className={`max-w-[88%] rounded-2xl px-3.5 py-2.5 text-sm whitespace-pre-wrap ${m.role === 'user' ? 'ms-auto bg-navy text-white rounded-ee-sm' : 'bg-bg dark:bg-white/10 rounded-es-sm'}`}>
              {m.content}
            </div>
            {m.fee_table && <div className="mt-2"><FeeTable fee={m.fee_table} compact /></div>}
            {m.sources?.length > 0 && <p className="mt-1 text-[11px] text-slate-500">Source: {m.sources.join(' · ')}</p>}
            {m.suggestions?.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {m.suggestions.map((s) => <button key={s} onClick={() => send(s)} className="rounded-full border border-gold/60 px-2.5 py-1 text-xs hover:bg-gold/10">{s}</button>)}
              </div>
            )}
          </div>
        ))}
        {loading && <div className="flex gap-1 px-2"><span className="typing-dot">●</span><span className="typing-dot">●</span><span className="typing-dot">●</span></div>}
      </div>

      <form onSubmit={(e) => { e.preventDefault(); send() }} className="flex gap-2 border-t border-slate-200 dark:border-white/10 p-3">
        <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="BS AI ki fee kitni hai?" className="flex-1 rounded-full border border-slate-300 dark:border-white/20 bg-transparent px-3.5 py-2 text-sm outline-none focus:border-gold" />
        <button disabled={loading} className="rounded-full bg-gold px-4 py-2 text-sm font-bold text-navy disabled:opacity-50">Send</button>
      </form>
    </div>
  )
}
