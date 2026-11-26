import { useEffect, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import api, { errorMessage } from '../api/client'
import FeeTable from '../components/FeeTable'
import { useAuth } from '../context/AuthContext'
import { useLanguage } from '../context/LanguageContext'

const DEFAULT_SUGGESTIONS = [
  'BS AI ki fee kitni hai?',
  'Admission ki last date kia hai?',
  'BS AI ke liye kitne marks chahiye?',
  'Merit kaise banta hai?',
  'Compare BS CS and BS AI fees',
  'بی ایس کمپیوٹر سائنس کی فیس کتنی ہے؟',
  'MPhil ke liye CGPA kitna chahiye?',
  'Canteen mein chicken burger kitne ka hai?',
  'University point kab chalta hai?',
  'Which programs can I join after FSc?',
]

function isUrduText(text) {
  // RTL only when Urdu script actually dominates — a Roman/English answer
  // that merely contains a few Urdu words (e.g. canteen item names) must
  // stay LTR, otherwise the whole bubble renders garbled.
  const t = text || ''
  const ur = (t.match(/[\u0600-\u06FF]/g) || []).length
  const lat = (t.match(/[a-zA-Z]/g) || []).length
  return ur > lat
}

export default function Chat() {
  const { user } = useAuth()
  const { t, lang } = useLanguage()
  const location = useLocation()
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Assalam-o-Alaikum! Main UniAssist hoon. Aap fees, programs aur admission ke baare mein English, اردو ya Roman Urdu mein sawal pooch sakte hain.\n\nHello! Ask me anything about IUB fees, programs and admissions.', suggestions: DEFAULT_SUGGESTIONS },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState(() => localStorage.getItem('chat_session') || null)
  const [listening, setListening] = useState(false)
  const [copiedId, setCopiedId] = useState(null)
  const [feedbackDone, setFeedbackDone] = useState({})
  const listRef = useRef(null)
  const sentPrefill = useRef(false)

  // Scroll ONLY the message list to the bottom. scrollIntoView() here used
  // to drag the whole page down on every message (the "chat goes down" bug).
  useEffect(() => {
    const el = listRef.current
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  }, [messages, loading])

  useEffect(() => {
    if (user) {
      api.get('/chat/history').then(({ data }) => {
        const items = data.items || data || []
        if (items.length) setMessages(items.map((m) => ({ role: m.role, content: m.content, message_id: m.id, sources: m.sources })))
      }).catch(() => {})
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    const prefill = location.state?.prefill
    if (prefill && !sentPrefill.current) { sentPrefill.current = true; send(prefill) }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.state])

  const send = async (text) => {
    const msg = (text ?? input).trim()
    if (!msg || loading) return
    setInput('')
    setMessages((m) => [...m, { role: 'user', content: msg }])
    setLoading(true)
    try {
      const { data } = await api.post('/chat', { message: msg, session_id: sessionId })
      if (data.session_id) { setSessionId(data.session_id); localStorage.setItem('chat_session', data.session_id) }
      setMessages((m) => [...m, {
        role: 'assistant', content: data.answer, language: data.language, intent: data.intent,
        sources: data.sources || [], fee_table: data.fee_table, message_id: data.message_id,
        suggestions: data.suggestions?.length ? data.suggestions : DEFAULT_SUGGESTIONS.slice(0, 3),
      }])
    } catch (err) {
      setMessages((m) => [...m, { role: 'assistant', content: errorMessage(err, 'Sorry, I could not answer right now. Please try again, or contact the university office.') }])
    } finally { setLoading(false) }
  }

  const feedback = async (msg, rating) => {
    if (!msg.message_id) { setFeedbackDone((f) => ({ ...f, [msg.content]: rating })); return }
    try { await api.post('/chat/feedback', { message_id: msg.message_id, rating, comment: '' }) } catch { /* still record locally */ }
    setFeedbackDone((f) => ({ ...f, [msg.message_id]: rating }))
  }

  const clearHistory = async () => {
    try { await api.delete('/chat/history') } catch { /* ignore */ }
    localStorage.removeItem('chat_session'); setSessionId(null)
    setMessages([{ role: 'assistant', content: 'Chat cleared. How can I help you?', suggestions: DEFAULT_SUGGESTIONS }])
  }

  const copyAnswer = async (msg) => {
    try { await navigator.clipboard.writeText(msg.content); setCopiedId(msg.message_id || msg.content); setTimeout(() => setCopiedId(null), 1500) } catch { /* clipboard unavailable */ }
  }

  const voiceInput = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) return
    const rec = new SR()
    rec.lang = lang === 'ur' ? 'ur-PK' : 'en-US'
    rec.interimResults = false
    rec.onstart = () => setListening(true)
    rec.onend = () => setListening(false)
    rec.onerror = () => setListening(false)
    rec.onresult = (e) => setInput(e.results[0][0].transcript)
    rec.start()
  }

  const hasVoice = typeof window !== 'undefined' && (window.SpeechRecognition || window.webkitSpeechRecognition)

  return (
    <div className="mx-auto flex max-w-4xl flex-col px-4 py-6" style={{ height: 'calc(100vh - 64px)' }}>
      <div className="flex items-center gap-3 rounded-t-2xl bg-navy px-5 py-4 text-white">
        <img src="/assets/iub-logo.jpg" alt="IUB" className="h-11 w-11 rounded-full bg-white object-contain" />
        <div className="flex-1">
          <h1 className="font-extrabold">UniAssist — AI Admissions &amp; Fee Chatbot</h1>
          <p className="text-xs text-gold-light">Answers from official Fall 2025 fee data · English / اردو / Roman Urdu</p>
        </div>
        {user && <button onClick={clearHistory} className="rounded-full border border-white/30 px-3 py-1.5 text-xs hover:bg-white/10">Clear history</button>}
      </div>

      <div ref={listRef} className="chat-scroll flex-1 overflow-y-auto border-x border-slate-200 dark:border-white/10 bg-white dark:bg-white/5 p-4 space-y-4">
        {messages.map((m, i) => {
          const urdu = isUrduText(m.content) || m.language === 'ur'
          return (
            <div key={m.message_id || i}>
              <div dir={urdu ? 'rtl' : 'ltr'} className={`max-w-[92%] sm:max-w-[80%] rounded-2xl px-4 py-3 text-[15px] whitespace-pre-wrap ${urdu ? 'urdu-text text-right' : ''} ${m.role === 'user' ? 'ms-auto bg-navy text-white rounded-ee-sm' : 'bg-bg dark:bg-white/10 rounded-es-sm'}`}>
                {m.content}
              </div>
              {m.fee_table && <div className="mt-2 max-w-[92%] sm:max-w-[80%]"><FeeTable fee={m.fee_table} compact /></div>}
              {m.role === 'assistant' && (
                <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                  {m.sources?.length > 0 && <span>{t('sources')}: {m.sources.join(' · ')}</span>}
                  {m.intent && <span className="rounded-full bg-slate-100 dark:bg-white/10 px-2 py-0.5">{m.intent}</span>}
                  <button onClick={() => copyAnswer(m)} className="hover:underline">{copiedId === (m.message_id || m.content) ? 'Copied ✓' : 'Copy'}</button>
                  {navigator.share && <button onClick={() => navigator.share({ text: m.content }).catch(() => {})} className="hover:underline">Share</button>}
                  <button disabled={!!feedbackDone[m.message_id]} onClick={() => feedback(m, 'up')} className="hover:scale-110" aria-label="Helpful">👍</button>
                  <button disabled={!!feedbackDone[m.message_id]} onClick={() => feedback(m, 'down')} className="hover:scale-110" aria-label="Not helpful">👎</button>
                  {feedbackDone[m.message_id] && <span className="text-emerald-600">Thanks for feedback</span>}
                </div>
              )}
              {m.suggestions?.length > 0 && i === messages.length - 1 && (
                <div className="mt-3">
                  <p className="text-xs font-semibold text-slate-400 mb-1.5">{t('suggestions')}</p>
                  <div className="flex flex-wrap gap-1.5">
                    {m.suggestions.map((s) => <button key={s} onClick={() => send(s)} className="rounded-full border border-gold/60 bg-gold/5 px-3 py-1.5 text-xs font-medium hover:bg-gold/15">{s}</button>)}
                  </div>
                </div>
              )}
            </div>
          )
        })}
        {loading && <div className="flex items-center gap-1.5 text-slate-400 text-sm"><span className="typing-dot">●</span><span className="typing-dot">●</span><span className="typing-dot">●</span> UniAssist is typing…</div>}
      </div>

      <form onSubmit={(e) => { e.preventDefault(); send() }} className="flex gap-2 rounded-b-2xl border border-slate-200 dark:border-white/10 bg-white dark:bg-white/5 p-3">
        <input value={input} onChange={(e) => setInput(e.target.value)} placeholder={t('typeMessage')} dir="auto"
          className="flex-1 rounded-full border border-slate-300 dark:border-white/20 bg-transparent px-4 py-2.5 text-sm outline-none focus:border-gold" />
        {hasVoice && <button type="button" onClick={voiceInput} className={`rounded-full border px-3.5 ${listening ? 'bg-red-100 border-red-300' : 'border-slate-300 dark:border-white/20'}`} aria-label="Voice input">🎤</button>}
        <button disabled={loading || !input.trim()} className="rounded-full bg-gold px-5 py-2.5 text-sm font-bold text-navy disabled:opacity-50">{t('send')}</button>
      </form>
      <p className="mt-2 text-center text-xs text-slate-400">{t('verifyNote')} Fees are never guessed — answers come from the structured database.</p>
    </div>
  )
}
