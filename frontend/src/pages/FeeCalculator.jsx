import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import api, { errorMessage, formatPKR } from '../api/client'

export default function FeeCalculator() {
  const location = useLocation()
  const [programs, setPrograms] = useState([])
  const [programId, setProgramId] = useState(location.state?.programId || '')
  const [semesters, setSemesters] = useState(8)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api.get('/programs', { params: { page: 1, page_size: 100 } }).then(({ data }) => setPrograms(data.items || [])).catch(() => {})
  }, [])

  const selected = programs.find((p) => String(p.id) === String(programId))

  const localEstimate = () => {
    if (!selected?.fee) return null
    const first = Number(selected.fee.total_first_semester || 0)
    const next = Number(selected.fee.total_next_semesters || 0)
    const n = Math.max(1, Number(semesters) || 1)
    return { total_estimate: first + next * (n - 1), breakdown: { first_semester: first, per_next_semester: next, remaining_semesters: n - 1, semesters: n } }
  }

  const calculate = async (e) => {
    e.preventDefault(); setError(''); setBusy(true)
    try {
      const { data } = await api.post('/tools/fee-calculator', { program_id: Number(programId), semesters: Number(semesters) })
      setResult(data)
    } catch (err) {
      const local = localEstimate()
      if (local) { setResult(local); setError('Live calculator unavailable — showing an estimate from published fee data.') }
      else setError(errorMessage(err, 'Could not calculate. Please select a program.'))
    } finally { setBusy(false) }
  }

  const input = 'w-full rounded-lg border border-slate-300 dark:border-white/20 bg-white dark:bg-white/5 px-3 py-2.5 text-sm'

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="text-3xl font-extrabold text-navy dark:text-white">Fee Calculator</h1>
      <p className="mt-1 text-slate-500">Choose a program and number of semesters to estimate your total degree cost (Fall 2025 fees).</p>

      <form onSubmit={calculate} className="mt-6 rounded-2xl bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 p-6 space-y-4">
        <label className="block text-sm font-semibold">Program
          <select required value={programId} onChange={(e) => setProgramId(e.target.value)} className={`${input} mt-1`}>
            <option value="">Select a program…</option>
            {programs.map((p) => <option key={p.id} value={p.id}>{p.name}{p.group ? ` (${p.group})` : ''} — {formatPKR(p.fee?.total_first_semester)} / 1st sem</option>)}
          </select>
        </label>
        <label className="block text-sm font-semibold">Number of Semesters: <span className="text-navy dark:text-gold">{semesters}</span>
          <input type="range" min="1" max="12" value={semesters} onChange={(e) => setSemesters(e.target.value)} className="mt-2 w-full accent-[#C9A227]" />
          <input type="number" min="1" max="12" value={semesters} onChange={(e) => setSemesters(e.target.value)} className={`${input} mt-1`} />
        </label>
        {selected?.fee && <p className="text-sm text-slate-500">1st semester: <b>{formatPKR(selected.fee.total_first_semester)}</b> · Next semesters: <b>{formatPKR(selected.fee.total_next_semesters)}</b> each</p>}
        <button disabled={busy || !programId} className="w-full rounded-lg bg-navy py-3 font-bold text-white disabled:opacity-50">{busy ? 'Calculating…' : 'Calculate Estimated Total'}</button>
        {error && <p className="rounded-lg bg-amber-50 text-amber-800 px-3 py-2 text-sm">{error}</p>}
      </form>

      {result && (
        <div className="mt-6 rounded-2xl bg-navy p-6 text-white">
          <p className="text-sm text-gold-light">Estimated Total — {selected?.name}</p>
          <p className="mt-1 text-4xl font-extrabold">{formatPKR(result.total_estimate)}</p>
          <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
            <div className="rounded-lg bg-white/10 p-3"><dt className="text-white/60">1st semester</dt><dd className="font-bold">{formatPKR(result.breakdown?.first_semester ?? result.breakdown?.first ?? selected?.fee?.total_first_semester)}</dd></div>
            <div className="rounded-lg bg-white/10 p-3"><dt className="text-white/60">Remaining semesters</dt><dd className="font-bold">{result.breakdown?.remaining_semesters ?? Math.max(0, Number(semesters) - 1)} × {formatPKR(result.breakdown?.per_next_semester ?? selected?.fee?.total_next_semesters)}</dd></div>
          </dl>
          {typeof result.breakdown === 'string' && <p className="mt-3 text-sm text-white/80">{result.breakdown}</p>}
          <p className="mt-4 text-xs text-white/60">Estimate only — excludes AC charges (Rs 2,000/semester where applicable), hostel, transport and any fee revision. Please verify with the official office.</p>
        </div>
      )}
    </div>
  )
}
