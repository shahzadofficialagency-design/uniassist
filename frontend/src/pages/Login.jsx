import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { errorMessage } from '../api/client'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [resetMsg, setResetMsg] = useState('')

  const submit = async (e) => {
    e.preventDefault(); setBusy(true); setError('')
    try {
      const data = await login(form.email, form.password)
      const dest = location.state?.from || (data.user?.role === 'admin' ? '/admin' : '/dashboard')
      navigate(dest, { replace: true })
    } catch (err) { setError(errorMessage(err, 'Login failed. Check your email and password.')) }
    finally { setBusy(false) }
  }

  return (
    <div className="relative min-h-[70vh]">
      <img src="/assets/iub-campus.jpg" alt="" className="absolute inset-0 h-full w-full object-cover" />
      <div className="absolute inset-0 bg-navy/80" />
      <div className="relative mx-auto flex max-w-md px-4 py-14">
        <form onSubmit={submit} className="w-full rounded-2xl bg-white dark:bg-[#1B154D] p-7 shadow-2xl">
          <div className="flex flex-col items-center text-center">
            <img src="/assets/iub-logo.jpg" alt="IUB" className="h-16 w-16 rounded-full object-contain" />
            <h1 className="mt-3 text-2xl font-extrabold text-navy dark:text-white">Welcome back</h1>
            <p className="text-sm text-slate-500">Login to UniAssist — IUB Student Portal</p>
          </div>
          {error && <p className="mt-4 rounded-lg bg-red-50 text-red-700 px-3 py-2 text-sm">{error}</p>}
          {resetMsg && <p className="mt-4 rounded-lg bg-emerald-50 text-emerald-700 px-3 py-2 text-sm">{resetMsg}</p>}
          <label className="mt-5 block text-sm font-semibold">Email<input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 dark:border-white/20 bg-transparent px-3 py-2.5" placeholder="you@example.com" /></label>
          <label className="mt-4 block text-sm font-semibold">Password<input type="password" required value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 dark:border-white/20 bg-transparent px-3 py-2.5" placeholder="••••••••" /></label>
          <button disabled={busy} className="mt-6 w-full rounded-lg bg-navy py-3 font-bold text-white hover:bg-navy-light disabled:opacity-50">{busy ? 'Logging in…' : 'Login'}</button>
          <button type="button" onClick={() => setResetMsg('If password reset is enabled by the admin, check your email for a reset link. Otherwise contact the university IT office.')} className="mt-3 w-full text-center text-sm text-navy dark:text-gold-light hover:underline">Forgot password?</button>
          <p className="mt-4 text-center text-sm text-slate-500">New student? <Link to="/register" className="font-bold text-navy dark:text-gold">Create an account</Link></p>
          <p className="mt-4 rounded-lg bg-bg dark:bg-white/5 p-3 text-xs text-slate-500">Demo accounts (if seeded): student@demo.iub.edu.pk / admin@iub.edu.pk — check the project README for passwords.</p>
        </form>
      </div>
    </div>
  )
}
