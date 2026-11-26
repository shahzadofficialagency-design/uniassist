import { useEffect, useRef, useState } from 'react'
import api, { errorMessage, formatPKR } from '../api/client'
import Skeleton from '../components/Skeleton'

function BarChart({ data, labelKey = 'label', valueKey = 'value', color = '#C9A227' }) {
  // Accept both arrays and {label: count} objects (e.g. language_distribution
  // from the API is an object) — crashing here once blanked the whole page.
  const asArray = Array.isArray(data)
    ? data
    : (data && typeof data === 'object'
        ? Object.entries(data).map(([k, v]) => ({ label: k, value: v }))
        : [])
  const rows = asArray.map((d) => ({
    label: d.label ?? d[labelKey] ?? d.date ?? d.question ?? d.language ?? d.name ?? '—',
    value: Number(d.value ?? d[valueKey] ?? d.count ?? d.total ?? d.queries ?? 0),
  }))
  const max = Math.max(...rows.map((r) => r.value), 1)
  if (!rows.length) return <p className="text-sm text-slate-500">No data yet.</p>
  return (
    <div className="space-y-2">
      {rows.slice(0, 10).map((r, i) => (
        <div key={i} className="flex items-center gap-2 text-xs">
          <span className="w-36 shrink-0 truncate text-slate-500" title={String(r.label)}>{String(r.label)}</span>
          <div className="h-4 flex-1 rounded bg-slate-100 dark:bg-white/10 overflow-hidden">
            <div className="h-full rounded" style={{ width: `${Math.max(3, (r.value / max) * 100)}%`, background: color }} />
          </div>
          <span className="w-10 text-right font-bold">{r.value}</span>
        </div>
      ))}
    </div>
  )
}

function Donut({ value, label }) {
  const pct = Math.max(0, Math.min(100, Number(value) || 0))
  const r = 34; const c = 2 * Math.PI * r
  return (
    <div className="flex items-center gap-4">
      <svg width="90" height="90" viewBox="0 0 90 90">
        <circle cx="45" cy="45" r={r} fill="none" stroke="#e5e0f5" strokeWidth="10" />
        <circle cx="45" cy="45" r={r} fill="none" stroke="#C9A227" strokeWidth="10" strokeLinecap="round"
          strokeDasharray={`${(pct / 100) * c} ${c}`} transform="rotate(-90 45 45)" />
        <text x="45" y="49" textAnchor="middle" fontSize="15" fontWeight="800" fill="currentColor">{pct}%</text>
      </svg>
      <p className="text-sm text-slate-500">{label}</p>
    </div>
  )
}

const TABS = ['Analytics', 'Programs', 'Fees', 'Faculties', 'Deadlines', 'Import', 'Unanswered']

export default function Admin() {
  const [tab, setTab] = useState('Analytics')
  const [analytics, setAnalytics] = useState(null)
  const [programs, setPrograms] = useState([])
  const [faculties, setFaculties] = useState([])
  const [deadlines, setDeadlines] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [importResult, setImportResult] = useState(null)
  const fileRef = useRef(null)

  const [progForm, setProgForm] = useState({ name: '', level: 'BS', group: '', shift: 'Morning', duration_years: 4, department_id: '' })
  const [feeForm, setFeeForm] = useState({ program_id: '', tuition_fee: '', other_dues: '', total_first_semester: '', total_next_semesters: '' })
  const [facForm, setFacForm] = useState({ name: '' })
  const [dlForm, setDlForm] = useState({ title: '', session: 'Fall 2025', opens_on: '', closes_on: '', description: '' })

  const loadAnalytics = () => api.get('/admin/analytics').then(({ data }) => setAnalytics(data)).catch((e) => setError(errorMessage(e, 'Could not load analytics.')))
  const loadPrograms = () => api.get('/programs', { params: { page: 1, page_size: 100 } }).then(({ data }) => setPrograms(data.items || [])).catch(() => {})
  const loadFaculties = () => api.get('/faculties').then(({ data }) => setFaculties(data.items || data || [])).catch(() => {})
  const loadDeadlines = () => api.get('/admin/deadlines').then(({ data }) => setDeadlines(data.items || data || [])).catch(() => setDeadlines([]))

  useEffect(() => {
    Promise.allSettled([loadAnalytics(), loadPrograms(), loadFaculties(), loadDeadlines()]).finally(() => setLoading(false))
  }, [])

  const flash = (m) => { setNotice(m); setTimeout(() => setNotice(''), 3500) }

  const createProgram = async (e) => {
    e.preventDefault()
    try { await api.post('/admin/programs', { ...progForm, duration_years: Number(progForm.duration_years), department_id: Number(progForm.department_id) || undefined }); flash('Program created.'); setProgForm({ name: '', level: 'BS', group: '', shift: 'Morning', duration_years: 4, department_id: '' }); loadPrograms() }
    catch (err) { setError(errorMessage(err)) }
  }
  const deleteProgram = async (id) => { if (!window.confirm('Delete this program?')) return; try { await api.delete(`/admin/programs/${id}`); loadPrograms(); flash('Program deleted.') } catch (err) { setError(errorMessage(err)) } }

  const saveFee = async (e) => {
    e.preventDefault()
    const payload = { program_id: Number(feeForm.program_id), tuition_fee: Number(feeForm.tuition_fee), other_dues: Number(feeForm.other_dues), total_first_semester: Number(feeForm.total_first_semester), total_next_semesters: Number(feeForm.total_next_semesters) }
    try { await api.post('/admin/fees', payload); flash('Fee saved.') } catch (err) { setError(errorMessage(err)) }
  }

  const createFaculty = async (e) => { e.preventDefault(); try { await api.post('/admin/faculties', facForm); setFacForm({ name: '' }); loadFaculties(); flash('Faculty created.') } catch (err) { setError(errorMessage(err)) } }
  const deleteFaculty = async (id) => { if (!window.confirm('Delete this faculty?')) return; try { await api.delete(`/admin/faculties/${id}`); loadFaculties() } catch (err) { setError(errorMessage(err)) } }

  const createDeadline = async (e) => { e.preventDefault(); try { await api.post('/admin/deadlines', dlForm); setDlForm({ title: '', session: 'Fall 2025', opens_on: '', closes_on: '', description: '' }); loadDeadlines(); flash('Deadline added.') } catch (err) { setError(errorMessage(err)) } }
  const deleteDeadline = async (id) => { try { await api.delete(`/admin/deadlines/${id}`); loadDeadlines() } catch (err) { setError(errorMessage(err)) } }

  const doImport = async (e) => {
    const file = e.target.files?.[0]; if (!file) return
    const fd = new FormData(); fd.append('file', file)
    setImportResult('Uploading & parsing…')
    try {
      const { data } = await api.post('/admin/import', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      setImportResult(`Import result: ${JSON.stringify(data)}`)
      loadPrograms(); loadFaculties()
    } catch (err) { setImportResult(`Import failed: ${errorMessage(err)}`) }
  }

  const exportUnanswered = async () => {
    try {
      const res = await api.get('/admin/unanswered/export', { responseType: 'blob' })
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a'); a.href = url; a.download = 'unanswered_questions.csv'; a.click()
      URL.revokeObjectURL(url)
    } catch (err) { setError(errorMessage(err, 'Export failed.')) }
  }

  const input = 'rounded-lg border border-slate-300 dark:border-white/20 bg-white dark:bg-white/5 px-3 py-2 text-sm w-full'
  const card = 'rounded-2xl bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 p-5'
  const feedbackPct = analytics ? Math.round(((analytics.feedback_ratio?.positive ?? analytics.feedback_ratio ?? 0) <= 1 ? (analytics.feedback_ratio?.positive ?? analytics.feedback_ratio ?? 0) * 100 : (analytics.feedback_ratio?.positive ?? analytics.feedback_ratio ?? 0))) : 0

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <div className="flex items-center gap-3">
        <img src="/assets/iub-logo.jpg" alt="" className="h-11 w-11 rounded-full bg-white object-contain" />
        <div><h1 className="text-3xl font-extrabold text-navy dark:text-white">Admin Panel</h1><p className="text-sm text-slate-500">Manage UniAssist data, imports and analytics.</p></div>
      </div>
      {notice && <p className="mt-4 rounded-lg bg-emerald-50 text-emerald-700 px-4 py-2.5 text-sm">{notice}</p>}
      {error && <p className="mt-4 rounded-lg bg-red-50 text-red-700 px-4 py-2.5 text-sm">{error} <button className="underline" onClick={() => setError('')}>Dismiss</button></p>}

      <div className="mt-5 flex flex-wrap gap-2">
        {TABS.map((tb) => <button key={tb} onClick={() => setTab(tb)} className={`rounded-full px-4 py-2 text-sm font-semibold ${tab === tb ? 'bg-navy text-white' : 'bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10'}`}>{tb}</button>)}
      </div>

      {loading ? <div className="mt-6 space-y-3"><Skeleton className="h-24" /><Skeleton className="h-48" /></div> : (
        <div className="mt-6">
          {tab === 'Analytics' && (
            <div className="space-y-6">
              <div className="grid gap-3 sm:grid-cols-3">
                <div className={card}><p className="text-sm text-slate-500">Total Users</p><p className="text-3xl font-extrabold text-navy dark:text-white">{analytics?.total_users ?? '—'}</p></div>
                <div className={card}><p className="text-sm text-slate-500">Total Chat Queries</p><p className="text-3xl font-extrabold text-navy dark:text-white">{analytics?.total_queries ?? '—'}</p></div>
                <div className={card}><p className="text-sm text-slate-500">Unanswered Questions</p><p className="text-3xl font-extrabold text-navy dark:text-white">{Array.isArray(analytics?.unanswered) ? analytics.unanswered.length : (analytics?.unanswered ?? '—')}</p></div>
              </div>
              <div className="grid gap-6 lg:grid-cols-2">
                <div className={card}><h3 className="mb-3 font-bold">Queries per Day</h3><BarChart data={analytics?.queries_per_day} labelKey="date" valueKey="count" color="#180F43" /></div>
                <div className={card}><h3 className="mb-3 font-bold">Language Distribution</h3><BarChart data={analytics?.language_distribution} labelKey="language" valueKey="count" /></div>
                <div className={card}><h3 className="mb-3 font-bold">Top Questions</h3><BarChart data={analytics?.top_questions} labelKey="question" valueKey="count" color="#2A2160" /></div>
                <div className={card}><h3 className="mb-3 font-bold">Most Viewed Programs</h3><BarChart data={analytics?.most_viewed_programs} labelKey="name" valueKey="views" /></div>
              </div>
              <div className={card}><h3 className="mb-3 font-bold">Feedback — Positive Ratio</h3><Donut value={feedbackPct} label="Share of 👍 ratings across all chatbot answers. Use the Unanswered tab to export questions the bot could not answer." /></div>
            </div>
          )}

          {tab === 'Programs' && (
            <div className="space-y-6">
              <form onSubmit={createProgram} className={`${card} grid gap-3 sm:grid-cols-3`}>
                <input required placeholder="Program name, e.g. BS Artificial Intelligence" value={progForm.name} onChange={(e) => setProgForm({ ...progForm, name: e.target.value })} className={`${input} sm:col-span-2`} />
                <select value={progForm.level} onChange={(e) => setProgForm({ ...progForm, level: e.target.value })} className={input}><option>BS</option><option>MS</option><option>PhD</option><option>Diploma</option></select>
                <input placeholder="Department ID" type="number" value={progForm.department_id} onChange={(e) => setProgForm({ ...progForm, department_id: e.target.value })} className={input} />
                <select value={progForm.group} onChange={(e) => setProgForm({ ...progForm, group: e.target.value })} className={input}><option value="">No group</option><option>Group-A</option><option>Group-B</option></select>
                <input placeholder="Duration (years)" type="number" step="0.5" value={progForm.duration_years} onChange={(e) => setProgForm({ ...progForm, duration_years: e.target.value })} className={input} />
                <button className="rounded-lg bg-navy py-2.5 font-bold text-white sm:col-span-3">Add Program</button>
              </form>
              <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-white/10 bg-white dark:bg-white/5">
                <table className="w-full min-w-[640px] text-sm"><thead><tr className="bg-navy text-white text-start"><th className="px-4 py-3 text-start">Program</th><th className="px-4 py-3 text-start">Level</th><th className="px-4 py-3 text-start">1st Sem Fee</th><th className="px-4 py-3" /></tr></thead>
                  <tbody>{programs.map((p) => <tr key={p.id} className="border-t border-slate-100 dark:border-white/5"><td className="px-4 py-2.5 font-medium">{p.name}</td><td className="px-4 py-2.5">{p.level}</td><td className="px-4 py-2.5">{formatPKR(p.fee?.total_first_semester)}</td><td className="px-4 py-2.5 text-right"><button onClick={() => deleteProgram(p.id)} className="text-red-600 font-semibold text-xs">Delete</button></td></tr>)}</tbody>
                </table>
                {programs.length === 0 && <p className="p-5 text-sm text-slate-500">No programs loaded.</p>}
              </div>
            </div>
          )}

          {tab === 'Fees' && (
            <form onSubmit={saveFee} className={`${card} grid gap-3 sm:grid-cols-2`}>
              <label className="text-sm font-semibold sm:col-span-2">Program<select required value={feeForm.program_id} onChange={(e) => setFeeForm({ ...feeForm, program_id: e.target.value })} className={`${input} mt-1`}><option value="">Select program…</option>{programs.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
              <label className="text-sm font-semibold">Tuition Fee (PKR)<input required type="number" value={feeForm.tuition_fee} onChange={(e) => setFeeForm({ ...feeForm, tuition_fee: e.target.value })} className={`${input} mt-1`} /></label>
              <label className="text-sm font-semibold">Other Dues (PKR)<input required type="number" value={feeForm.other_dues} onChange={(e) => setFeeForm({ ...feeForm, other_dues: e.target.value })} className={`${input} mt-1`} /></label>
              <label className="text-sm font-semibold">Total — 1st Semester<input required type="number" value={feeForm.total_first_semester} onChange={(e) => setFeeForm({ ...feeForm, total_first_semester: e.target.value })} className={`${input} mt-1`} /></label>
              <label className="text-sm font-semibold">Total — Next Semesters<input required type="number" value={feeForm.total_next_semesters} onChange={(e) => setFeeForm({ ...feeForm, total_next_semesters: e.target.value })} className={`${input} mt-1`} /></label>
              <button className="rounded-lg bg-gold py-2.5 font-bold text-navy sm:col-span-2">Save Fee Structure</button>
              <p className="text-xs text-slate-500 sm:col-span-2">Tip: 1st semester total should equal tuition + other dues. Requirements (marks, seats, documents) can be managed via the backend API at /api/admin/requirements.</p>
            </form>
          )}

          {tab === 'Faculties' && (
            <div className="space-y-6">
              <form onSubmit={createFaculty} className={`${card} flex gap-3`}><input required placeholder="New faculty name" value={facForm.name} onChange={(e) => setFacForm({ name: e.target.value })} className={input} /><button className="shrink-0 rounded-lg bg-navy px-5 font-bold text-white">Add</button></form>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{faculties.map((f) => <div key={f.id} className={`${card} flex items-center justify-between`}><span className="font-semibold">{f.name}</span><button onClick={() => deleteFaculty(f.id)} className="text-xs font-semibold text-red-600">Delete</button></div>)}</div>
              {faculties.length === 0 && <p className="text-slate-500">No faculties loaded.</p>}
            </div>
          )}

          {tab === 'Deadlines' && (
            <div className="space-y-6">
              <form onSubmit={createDeadline} className={`${card} grid gap-3 sm:grid-cols-2`}>
                <input required placeholder="Title, e.g. Fall 2026 Admissions" value={dlForm.title} onChange={(e) => setDlForm({ ...dlForm, title: e.target.value })} className={input} />
                <input placeholder="Session" value={dlForm.session} onChange={(e) => setDlForm({ ...dlForm, session: e.target.value })} className={input} />
                <label className="text-sm">Opens<input type="date" value={dlForm.opens_on} onChange={(e) => setDlForm({ ...dlForm, opens_on: e.target.value })} className={`${input} mt-1`} /></label>
                <label className="text-sm">Closes<input type="date" value={dlForm.closes_on} onChange={(e) => setDlForm({ ...dlForm, closes_on: e.target.value })} className={`${input} mt-1`} /></label>
                <input placeholder="Description" value={dlForm.description} onChange={(e) => setDlForm({ ...dlForm, description: e.target.value })} className={`${input} sm:col-span-2`} />
                <button className="rounded-lg bg-navy py-2.5 font-bold text-white sm:col-span-2">Add Deadline</button>
              </form>
              {deadlines.length === 0 ? <p className="text-slate-500">No deadlines yet — deadlines are not in the fee PDF, so add only officially announced dates here.</p> : (
                <ul className="space-y-2">{deadlines.map((d) => <li key={d.id} className={`${card} flex items-center justify-between`}><span><b>{d.title}</b> <span className="text-slate-500 text-sm">{d.opens_on || ''} → {d.closes_on || ''}</span></span><button onClick={() => deleteDeadline(d.id)} className="text-xs font-semibold text-red-600">Delete</button></li>)}</ul>
              )}
            </div>
          )}

          {tab === 'Import' && (
            <div className={card}>
              <h3 className="font-bold">Import Data (Excel / CSV / PDF / DOCX)</h3>
              <p className="mt-1 text-sm text-slate-500">Upload a fee or program file. The backend parses it, and the new data is indexed without a restart. Always review imported fees before relying on them.</p>
              <input ref={fileRef} type="file" accept=".xlsx,.xls,.csv,.pdf,.docx" onChange={doImport} className="mt-4 block w-full text-sm" />
              {importResult && <pre className="mt-4 whitespace-pre-wrap rounded-lg bg-bg dark:bg-white/10 p-4 text-xs">{importResult}</pre>}
            </div>
          )}

          {tab === 'Unanswered' && (
            <div className={card}>
              <h3 className="font-bold">Unanswered Questions</h3>
              <p className="mt-1 text-sm text-slate-500">Questions the chatbot could not answer from the database. Export them, add the missing data above, and the bot will answer next time.</p>
              <ul className="mt-4 space-y-2">
                {(Array.isArray(analytics?.unanswered) ? analytics.unanswered : []).map((q, i) => <li key={i} className="rounded-lg bg-bg dark:bg-white/10 px-4 py-2.5 text-sm">{typeof q === 'string' ? q : (q.question || JSON.stringify(q))}</li>)}
              </ul>
              {(!analytics?.unanswered || analytics.unanswered.length === 0) && <p className="mt-3 text-sm text-slate-500">No unanswered questions recorded.</p>}
              <button onClick={exportUnanswered} className="mt-5 rounded-lg bg-navy px-5 py-2.5 font-bold text-white">Export Unanswered (CSV) ↓</button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
