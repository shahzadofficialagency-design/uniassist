import { useEffect, useState } from 'react'
import api, { errorMessage } from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function Profile() {
  const { user, setUser, fetchMe } = useAuth()
  const [programs, setPrograms] = useState([])
  const [form, setForm] = useState({ name: '', phone: '', city: '', matric_marks: '', inter_marks: '', interested_program_id: '' })
  const [msg, setMsg] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [historyCount, setHistoryCount] = useState(null)

  useEffect(() => {
    if (user) setForm({
      name: user.name || '', phone: user.phone || '', city: user.city || '',
      matric_marks: user.matric_marks ?? '', inter_marks: user.inter_marks ?? '',
      interested_program_id: user.interested_program_id ?? '',
    })
  }, [user])

  useEffect(() => {
    api.get('/programs', { params: { page: 1, page_size: 100 } }).then(({ data }) => setPrograms(data.items || [])).catch(() => {})
    api.get('/chat/history').then(({ data }) => setHistoryCount((data.items || data || []).length)).catch(() => setHistoryCount(0))
  }, [])

  const save = async (e) => {
    e.preventDefault(); setBusy(true); setMsg(''); setError('')
    const payload = {
      name: form.name, phone: form.phone, city: form.city,
      matric_marks: form.matric_marks === '' ? null : Number(form.matric_marks),
      inter_marks: form.inter_marks === '' ? null : Number(form.inter_marks),
      interested_program_id: form.interested_program_id === '' ? null : Number(form.interested_program_id),
    }
    try {
      const { data } = await api.put('/auth/me', payload)
      setUser(data); localStorage.setItem('user', JSON.stringify(data)); setMsg('Profile saved successfully.')
    } catch {
      // Backend may only expose GET /auth/me — keep the values locally so the UI still works.
      try { await api.patch('/auth/me', payload); await fetchMe(); setMsg('Profile saved successfully.') }
      catch (err2) { setError(errorMessage(err2, 'Profile update endpoint is not available on the backend yet. Your account details below are unchanged.')) }
    } finally { setBusy(false) }
  }

  const clearChat = async () => {
    try { await api.delete('/chat/history'); setHistoryCount(0); setMsg('Chat history deleted.') } catch (err) { setError(errorMessage(err)) }
  }

  const input = 'mt-1 w-full rounded-lg border border-slate-300 dark:border-white/20 bg-transparent px-3 py-2.5 text-sm'
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <div className="rounded-2xl bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 p-7">
        <div className="flex items-center gap-4">
          <span className="grid h-16 w-16 place-items-center rounded-full bg-navy text-2xl font-extrabold text-gold">{(user?.name || 'S')[0]}</span>
          <div>
            <h1 className="text-2xl font-extrabold text-navy dark:text-white">{user?.name}</h1>
            <p className="text-sm text-slate-500">{user?.email} · Role: {user?.role}</p>
          </div>
        </div>
        {msg && <p className="mt-4 rounded-lg bg-emerald-50 text-emerald-700 px-3 py-2 text-sm">{msg}</p>}
        {error && <p className="mt-4 rounded-lg bg-amber-50 text-amber-800 px-3 py-2 text-sm">{error}</p>}
        <form onSubmit={save} className="mt-6 grid gap-4 sm:grid-cols-2">
          <label className="text-sm font-semibold">Full Name<input value={form.name} onChange={set('name')} className={input} /></label>
          <label className="text-sm font-semibold">Phone<input value={form.phone} onChange={set('phone')} className={input} /></label>
          <label className="text-sm font-semibold">City<input value={form.city} onChange={set('city')} className={input} /></label>
          <label className="text-sm font-semibold">Interested Program
            <select value={form.interested_program_id} onChange={set('interested_program_id')} className={input}>
              <option value="">None</option>
              {programs.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </label>
          <label className="text-sm font-semibold">Matric Marks<input type="number" value={form.matric_marks} onChange={set('matric_marks')} className={input} /></label>
          <label className="text-sm font-semibold">Intermediate Marks<input type="number" value={form.inter_marks} onChange={set('inter_marks')} className={input} /></label>
          <button disabled={busy} className="sm:col-span-2 rounded-lg bg-navy py-3 font-bold text-white disabled:opacity-50">{busy ? 'Saving…' : 'Save Profile'}</button>
        </form>

        <div className="mt-8 border-t border-slate-200 dark:border-white/10 pt-5">
          <h2 className="font-bold text-navy dark:text-white">Chat History</h2>
          <p className="mt-1 text-sm text-slate-500">{historyCount === null ? 'Loading…' : `${historyCount} saved message(s). Your history is private to your account.`}</p>
          <button onClick={clearChat} className="mt-3 rounded-lg border border-red-300 text-red-600 px-4 py-2 text-sm font-semibold hover:bg-red-50">Delete Chat History</button>
        </div>
      </div>
    </div>
  )
}
