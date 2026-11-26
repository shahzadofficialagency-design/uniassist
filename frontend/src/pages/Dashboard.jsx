import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'
import ProgramCard from '../components/ProgramCard'
import Skeleton, { PageSkeleton } from '../components/Skeleton'
import { useAuth } from '../context/AuthContext'

export default function Dashboard() {
  const { user } = useAuth()
  const [history, setHistory] = useState([])
  const [programs, setPrograms] = useState([])
  const [announcements, setAnnouncements] = useState([])
  const [deadlines, setDeadlines] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.allSettled([api.get('/chat/history'), api.get('/programs', { params: { page_size: 6 } }), api.get('/announcements'), api.get('/deadlines')])
      .then(([h, p, a, d]) => {
        if (h.status === 'fulfilled') setHistory(h.value.data?.items || h.value.data || [])
        if (p.status === 'fulfilled') setPrograms(p.value.data?.items || [])
        if (a.status === 'fulfilled') setAnnouncements(a.value.data?.items || a.value.data || [])
        if (d.status === 'fulfilled') setDeadlines(d.value.data?.items || d.value.data || [])
        setLoading(false)
      })
  }, [])

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <div className="rounded-2xl bg-navy p-6 text-white flex flex-wrap items-center gap-4">
        <img src="/assets/iub-logo.jpg" alt="" className="h-14 w-14 rounded-full bg-white object-contain" />
        <div className="flex-1">
          <h1 className="text-2xl font-extrabold">Assalam-o-Alaikum, {user?.name || 'Student'} 👋</h1>
          <p className="text-sm text-white/75">{user?.email} {user?.city ? `· ${user.city}` : ''} — explore programs, calculate fees or ask UniAssist anything.</p>
        </div>
        <Link to="/chat" className="rounded-full bg-gold px-5 py-2.5 font-bold text-navy">Ask UniAssist</Link>
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-4">
        {[
          ['/programs', '🎓', 'Browse Programs', '457 programs, 14 faculties'],
          ['/fee-calculator', '🧮', 'Fee Calculator', 'Estimate your total degree cost'],
          ['/eligibility', '✅', 'Eligibility Checker', 'See what you qualify for'],
          ['/compare', '⚖️', 'Compare Programs', 'Fees & duration side by side'],
        ].map(([to, icon, title, sub]) => (
          <Link key={to} to={to} className="rounded-2xl border border-slate-200 dark:border-white/10 bg-white dark:bg-white/5 p-4 hover:border-gold hover:shadow transition">
            <span className="text-2xl">{icon}</span>
            <p className="mt-2 font-bold text-navy dark:text-white">{title}</p>
            <p className="text-sm text-slate-500">{sub}</p>
          </Link>
        ))}
      </div>

      <div className="mt-8 grid gap-8 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between"><h2 className="text-xl font-extrabold text-navy dark:text-white">Featured Programs</h2><Link to="/programs" className="text-sm font-semibold text-navy dark:text-gold">View all →</Link></div>
          <div className="mt-4">
            {loading ? <PageSkeleton cards={3} /> : programs.length === 0 ? <p className="text-slate-500">No programs loaded yet.</p> : (
              <div className="grid gap-4 sm:grid-cols-2">{programs.slice(0, 4).map((p) => <ProgramCard key={p.id} program={p} />)}</div>
            )}
          </div>
          <h2 className="mt-8 text-xl font-extrabold text-navy dark:text-white">Recent Chat</h2>
          {loading ? <div className="mt-3 space-y-2"><Skeleton /><Skeleton /></div> : history.length === 0 ? (
            <p className="mt-3 text-sm text-slate-500">No chats yet. <Link to="/chat" className="font-semibold underline">Start your first conversation</Link> — try “BS AI ki fee kitni hai?”</p>
          ) : (
            <ul className="mt-3 space-y-2">
              {history.slice(0, 5).map((h, i) => (
                <li key={h.id || i} className="rounded-xl bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 px-4 py-3 text-sm">
                  <span className="font-semibold">{h.role === 'user' ? 'You: ' : 'UniAssist: '}</span>{String(h.content || h.message || '').slice(0, 160)}
                </li>
              ))}
            </ul>
          )}
        </div>
        <aside className="space-y-6">
        <div className="rounded-2xl bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 p-5 h-fit">
          <h3 className="font-extrabold text-navy dark:text-white">📅 Admission Deadlines</h3>
          {deadlines.length === 0 ? <p className="mt-2 text-sm text-slate-500">No deadlines published right now.</p> : (
            <ul className="mt-3 space-y-3">{deadlines.map((d) => (
              <li key={d.id} className="border-s-4 border-gold ps-3">
                <p className="text-sm font-semibold">{d.title}</p>
                <p className="text-sm text-slate-500">Last date: <span className="font-bold text-navy dark:text-gold">{d.closes_on}</span> · {d.session}</p>
              </li>
            ))}</ul>
          )}
          <p className="mt-3 text-[11px] text-slate-400">Source: IUB official website (iub.edu.pk)</p>
        </div>
        <div className="rounded-2xl bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 p-5 h-fit">
          <h3 className="font-extrabold text-navy dark:text-white">Announcements</h3>
          {announcements.length === 0 ? <p className="mt-2 text-sm text-slate-500">No announcements. Current fee session: Fall 2025 (new intake).</p> : (
            <ul className="mt-3 space-y-3">{announcements.map((a) => <li key={a.id} className="border-s-4 border-gold ps-3"><p className="text-sm font-semibold">{a.title}</p><p className="text-sm text-slate-500">{a.body}</p></li>)}</ul>
          )}
          <Link to="/profile" className="mt-5 block rounded-lg bg-bg dark:bg-white/10 px-4 py-2.5 text-center text-sm font-semibold">Edit Profile & Marks</Link>
        </div>
        </aside>
      </div>
    </div>
  )
}
