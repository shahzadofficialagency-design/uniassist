import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api, { errorMessage } from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [programs, setPrograms] = useState([])
  const [form, setForm] = useState({ name: '', email: '', phone: '', city: '', password: '', matric_marks: '', inter_marks: '', interested_program_id: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api.get('/programs', { params: { page: 1, page_size: 100 } })
      .then(({ data }) => setPrograms(data.items || data || []))
      .catch(() => setPrograms([]))
  }, [])

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault(); setBusy(true); setError('')
    const payload = {
      ...form,
      matric_marks: form.matric_marks === '' ? null : Number(form.matric_marks),
      inter_marks: form.inter_marks === '' ? null : Number(form.inter_marks),
      interested_program_id: form.interested_program_id === '' ? null : Number(form.interested_program_id),
    }
    try {
      await register(payload)
      navigate('/dashboard')
    } catch (err) { setError(errorMessage(err, 'Registration failed. Please check your details.')) }
    finally { setBusy(false) }
  }

  const input = 'mt-1 w-full rounded-lg border border-slate-300 dark:border-white/20 bg-transparent px-3 py-2.5 text-sm'
  return (
    <div className="mx-auto max-w-2xl px-4 py-10">
      <div className="rounded-2xl bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 p-7 shadow-sm">
        <div className="flex items-center gap-3">
          <img src="/assets/iub-logo.jpg" alt="IUB" className="h-12 w-12 rounded-full object-contain" />
          <div><h1 className="text-2xl font-extrabold text-navy dark:text-white">Create your account</h1><p className="text-sm text-slate-500">Register as a student on UniAssist</p></div>
        </div>
        {error && <p className="mt-4 rounded-lg bg-red-50 text-red-700 px-3 py-2 text-sm">{error}</p>}
        <form onSubmit={submit} className="mt-5 grid gap-4 sm:grid-cols-2">
          <label className="text-sm font-semibold">Full Name *<input required value={form.name} onChange={set('name')} className={input} /></label>
          <label className="text-sm font-semibold">Email *<input type="email" required value={form.email} onChange={set('email')} className={input} /></label>
          <label className="text-sm font-semibold">Phone<input value={form.phone} onChange={set('phone')} className={input} placeholder="03xx-xxxxxxx" /></label>
          <label className="text-sm font-semibold">City<input value={form.city} onChange={set('city')} className={input} placeholder="Bahawalpur" /></label>
          <label className="text-sm font-semibold">Password *<input type="password" required minLength={6} value={form.password} onChange={set('password')} className={input} /></label>
          <label className="text-sm font-semibold">Interested Program
            <select value={form.interested_program_id} onChange={set('interested_program_id')} className={input}>
              <option value="">Select (optional)</option>
              {programs.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </label>
          <label className="text-sm font-semibold">Matric Marks<input type="number" min="0" value={form.matric_marks} onChange={set('matric_marks')} className={input} /></label>
          <label className="text-sm font-semibold">Intermediate Marks<input type="number" min="0" value={form.inter_marks} onChange={set('inter_marks')} className={input} /></label>
          <button disabled={busy} className="sm:col-span-2 rounded-lg bg-gold py-3 font-bold text-navy disabled:opacity-50">{busy ? 'Creating account…' : 'Register'}</button>
        </form>
        <p className="mt-4 text-center text-sm text-slate-500">Already registered? <Link to="/login" className="font-bold text-navy dark:text-gold">Login</Link></p>
      </div>
    </div>
  )
}
