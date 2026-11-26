import { useState } from 'react'
import { Link } from 'react-router-dom'
import api, { errorMessage } from '../api/client'
import ProgramCard from '../components/ProgramCard'
import { PageSkeleton } from '../components/Skeleton'
import { btnGold, btnPrimarySm } from '../components/ui'

const MAX_SHOWN = 12

export default function EligibilityChecker() {
  const [form, setForm] = useState({ level: 'BS', marks_pct: '', cgpa: '', stream: 'FSc Pre-Engineering' })
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const isPhd = form.level === 'PhD'

  const submit = async (e) => {
    e.preventDefault(); setBusy(true); setError(''); setResult(null)
    try {
      const payload = isPhd
        ? { level: form.level, cgpa: Number(form.cgpa), stream: form.stream }
        : { level: form.level, marks_pct: Number(form.marks_pct), stream: form.stream }
      const { data } = await api.post('/tools/eligibility', payload)
      setResult(data)
    } catch (err) { setError(errorMessage(err, 'Eligibility check failed. Please try again.')) }
    finally { setBusy(false) }
  }

  const input = 'w-full rounded-lg border border-slate-300 dark:border-white/20 bg-white dark:bg-white/5 px-3 py-2.5 text-sm mt-1'

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="text-3xl font-extrabold text-navy dark:text-white">Eligibility Checker</h1>
      <p className="mt-1 text-slate-500">Enter your qualification level, marks and stream — always verify final eligibility with the admission office.</p>

      <div className="mt-4 rounded-2xl border border-gold/60 bg-gold/5 px-5 py-4 text-sm">
        <p className="font-extrabold text-navy dark:text-gold">📌 Portal admission rule</p>
        <ul className="mt-1 list-disc ps-5 space-y-0.5 text-slate-600 dark:text-slate-300">
          <li><b>BS / Bachelor:</b> at least <b>70% marks</b> in Intermediate (11th + 12th combined) — below 70%, admission is not possible under this rule.</li>
          <li><b>PhD:</b> CGPA of at least <b>3.7</b> in MS/MPhil.</li>
          <li className="text-xs text-slate-500">This is the portal's general rule. Official programme-wise criteria (from iub.edu.pk) may differ and are shown on each program's page.</li>
        </ul>
      </div>

      <form onSubmit={submit} className="mt-6 grid gap-4 rounded-2xl bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 p-6 sm:grid-cols-3">
        <label className="text-sm font-semibold">Apply for Level
          <select value={form.level} onChange={(e) => setForm({ ...form, level: e.target.value })} className={input}>
            <option value="BS">BS / Undergraduate</option><option value="MS">MS / MPhil</option><option value="PhD">PhD</option><option value="Diploma">Diploma / Certificate</option>
          </select>
        </label>
        {isPhd ? (
          <label className="text-sm font-semibold">Your CGPA (in MS/MPhil)
            <input type="number" min="0" max="4" step="0.01" required value={form.cgpa} onChange={(e) => setForm({ ...form, cgpa: e.target.value })} placeholder="e.g. 3.80" className={input} />
          </label>
        ) : (
          <label className="text-sm font-semibold">{form.level === 'BS' ? 'Your Intermediate Marks (%) — 11th + 12th combined' : 'Your Marks (%)'}
            <input type="number" min="0" max="100" step="0.1" required value={form.marks_pct} onChange={(e) => setForm({ ...form, marks_pct: e.target.value })} placeholder="e.g. 72" className={input} />
          </label>
        )}
        <label className="text-sm font-semibold">Stream / Prior Qualification
          <select value={form.stream} onChange={(e) => setForm({ ...form, stream: e.target.value })} className={input}>
            <option>FSc Pre-Engineering</option><option>FSc Pre-Medical</option><option>ICS (Computer Science)</option>
            <option>FA / Humanities</option><option>ICom / Commerce</option><option>A-Levels</option>
            <option>Bachelor (BS/BA/BSc)</option><option>Master (MA/MSc)</option><option>MS / MPhil</option>
          </select>
        </label>
        <button disabled={busy} className={`${btnGold} sm:col-span-3 w-full py-3 text-base`}>{busy ? 'Checking…' : 'Check Eligibility'}</button>
        {error && <p className="sm:col-span-3 rounded-lg bg-red-50 text-red-700 px-3 py-2 text-sm">{error}</p>}
      </form>

      <div className="mt-8">
        {busy ? <PageSkeleton cards={3} /> : result ? (
          <>
            {/* Big, clear verdict — admission possible or not, at a glance */}
            {result.rule ? (
              <div className={`rounded-2xl border-2 p-5 ${result.rule.passed ? 'border-emerald-400 bg-emerald-50 dark:bg-emerald-900/20' : 'border-red-400 bg-red-50 dark:bg-red-900/20'}`}>
                <p className={`text-xl font-extrabold ${result.rule.passed ? 'text-emerald-700 dark:text-emerald-300' : 'text-red-700 dark:text-red-300'}`}>
                  {result.rule.passed
                    ? (result.rule.type === 'phd_cgpa'
                        ? `✅ Admission is possible — your CGPA ${result.rule.value} meets the PhD rule (≥ ${result.rule.threshold})`
                        : `✅ Admission is possible — your marks ${result.rule.value}% meet the BS rule (≥ ${result.rule.threshold}% in Intermediate)`)
                    : (result.rule.type === 'phd_cgpa'
                        ? `❌ Admission is NOT possible under the portal rule — PhD needs CGPA ≥ ${result.rule.threshold}, yours is ${result.rule.value}`
                        : `❌ Admission is NOT possible under the portal rule — BS needs at least ${result.rule.threshold}% in Intermediate, yours is ${result.rule.value}%`)}
                </p>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                  {result.rule.passed
                    ? `${(result.eligible || []).length} program(s) match your level below. Official programme-wise criteria may differ — verify with the admission office.`
                    : 'This is the portal\u2019s general rule. Official programme-wise criteria are shown on each program\u2019s page — please also verify with the university office.'}
                </p>
              </div>
            ) : (
              <div className="rounded-2xl border-2 border-navy/20 bg-navy/5 p-5">
                <p className="text-xl font-extrabold text-navy dark:text-white">📋 {(result.eligible || []).length} program(s) match your level</p>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">No general portal rule applies to this level — official programme-wise criteria are shown on each program's page.</p>
              </div>
            )}
            {result.note && <p className="mt-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 text-amber-800 dark:text-amber-200 px-4 py-2.5 text-sm">{result.note}</p>}
            {(result.eligible || []).length > 0 && (
              <>
                <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {result.eligible.slice(0, MAX_SHOWN).map((p) => <ProgramCard key={p.id} program={p} />)}
                </div>
                {result.eligible.length > MAX_SHOWN && (
                  <div className="mt-5 flex flex-wrap items-center gap-3 rounded-xl bg-navy/5 dark:bg-white/5 px-4 py-3">
                    <span className="text-sm font-semibold text-navy dark:text-white">Showing {MAX_SHOWN} of {result.eligible.length} matching programs</span>
                    <Link to={`/programs?level=${form.level}`} className={btnPrimarySm}>View all {form.level} programs →</Link>
                  </div>
                )}
              </>
            )}
          </>
        ) : null}
      </div>
    </div>
  )
}
