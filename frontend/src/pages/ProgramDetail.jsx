import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import api, { errorMessage, formatPKR } from '../api/client'
import FeeTable from '../components/FeeTable'
import Skeleton from '../components/Skeleton'
import { btnOutlineSm, btnPrimarySm } from '../components/ui'

export default function ProgramDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [program, setProgram] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get(`/programs/${id}`).then(({ data }) => setProgram(data)).catch((e) => setError(errorMessage(e, 'Program not found.'))).finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="mx-auto max-w-4xl px-4 py-10 space-y-3"><Skeleton className="h-9 w-2/3" /><Skeleton /><Skeleton className="h-40" /></div>
  if (error || !program) return <div className="mx-auto max-w-4xl px-4 py-10"><div className="rounded-2xl bg-red-50 text-red-700 p-6">{error || 'Program not found.'} <Link to="/programs" className="underline font-semibold">Back to programs</Link></div></div>

  const req = program.requirement || {}
  const docs = Array.isArray(req.documents) ? req.documents : (req.documents ? String(req.documents).split(',').map((s) => s.trim()).filter(Boolean) : [])

  const addCompare = () => {
    const cur = JSON.parse(localStorage.getItem('compare') || '[]')
    const next = [...new Set([...cur, program.id])].slice(-3)
    localStorage.setItem('compare', JSON.stringify(next))
    navigate(`/compare?ids=${next.join(',')}`)
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <Link to="/programs" className="text-sm font-semibold text-navy dark:text-gold">← All Programs</Link>
      <div className="mt-4 rounded-2xl bg-navy p-6 text-white">
        <div className="flex flex-wrap gap-2 text-xs font-semibold">
          <span className="rounded-full bg-white/15 px-3 py-1">{program.level}</span>
          {program.group && <span className="rounded-full bg-gold px-3 py-1 text-navy">{program.group}</span>}
          {program.shift && <span className="rounded-full bg-white/15 px-3 py-1">{program.shift}</span>}
        </div>
        <h1 className="mt-3 text-3xl font-extrabold">{program.name}</h1>
        <p className="mt-1 text-white/75">{program.department} · {program.faculty}</p>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-3 space-y-6">
          <section className="rounded-2xl bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 p-6">
            <h2 className="font-extrabold text-navy dark:text-white">Fee Structure — Fall 2025</h2>
            <div className="mt-4"><FeeTable fee={program.fee} /></div>
            <p className="mt-3 text-xs text-slate-500">Group-A / Group-B meaning is not defined in the official fee PDF — please confirm with the university office. AC charges (Rs 2,000/semester) may apply where available.</p>
            <div className="mt-4 flex flex-wrap gap-2">
              <Link to="/fee-calculator" state={{ programId: program.id }} className={btnPrimarySm}>Calculate Total Cost</Link>
              <button onClick={addCompare} className={btnOutlineSm}>Add to Compare</button>
              <Link to="/chat" state={{ prefill: `What is the fee for ${program.name}?` }} className={btnOutlineSm}>Ask Chatbot</Link>
            </div>
          </section>

          <section className="rounded-2xl bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 p-6">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="font-extrabold text-navy dark:text-white">Admission Requirements</h2>
              {req.prior_qualification_source === 'iub_official_web' && (
                <span className="rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300 px-3 py-1 text-[11px] font-bold">Source: IUB official website (iub.edu.pk)</span>
              )}
            </div>
            <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
              <div><dt className="text-slate-500">Prior Qualification</dt><dd className="font-semibold">{req.prior_qualification || 'Not available in provided data — verify with office'}</dd></div>
              <div><dt className="text-slate-500">Minimum Marks</dt><dd className="font-semibold">{req.min_marks_pct != null ? `${req.min_marks_pct}%` : 'Not specified in official data'}</dd></div>
              <div><dt className="text-slate-500">Entry Test</dt><dd className="font-semibold">{req.entry_test || 'Not specified in official data'}</dd></div>
              <div><dt className="text-slate-500">Merit Formula</dt><dd className="font-semibold">{req.merit_formula || 'Not specified in official data'}</dd></div>
              <div><dt className="text-slate-500">Seats</dt><dd className="font-semibold">{req.seats ?? 'Not specified in provided data'}</dd></div>
              <div><dt className="text-slate-500">Duration</dt><dd className="font-semibold">{program.duration_years ? `${program.duration_years} years` : '—'}</dd></div>
            </dl>
            <h3 className="mt-5 font-bold">Required Documents</h3>
            {docs.length ? <ul className="mt-2 list-disc ps-5 text-sm space-y-1">{docs.map((d) => <li key={d}>{d}</li>)}</ul> : <p className="mt-2 text-sm text-slate-500">Document list is not included in the fee structure PDF. The admin can add it from the Admin Panel; until then, please confirm with the admission office.</p>}
          </section>
        </div>

        <aside className="lg:col-span-2 space-y-4">
          <div className="rounded-2xl border border-gold/50 bg-gold-light/20 p-5">
            <p className="text-sm text-slate-600 dark:text-slate-200">First semester total</p>
            <p className="text-3xl font-extrabold text-navy dark:text-white">{formatPKR(program.fee?.total_first_semester)}</p>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">Then {formatPKR(program.fee?.total_next_semesters)} per semester</p>
          </div>
          <Link to="/eligibility" className="block rounded-2xl bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 p-5 hover:border-gold">
            <p className="font-bold text-navy dark:text-white">Check your eligibility →</p>
            <p className="text-sm text-slate-500">Enter your marks and see all programs you qualify for.</p>
          </Link>
        </aside>
      </div>
    </div>
  )
}
