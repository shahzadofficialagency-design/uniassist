import { useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import api, { formatPKR } from '../api/client'
import Skeleton from '../components/Skeleton'
import { btnGoldSm, btnOutlineSm } from '../components/ui'

const MAX_COMPARE = 3

export default function Compare() {
  const [params, setParams] = useSearchParams()
  const [programs, setPrograms] = useState([])
  const [loading, setLoading] = useState(false)
  const [query, setQuery] = useState('')
  const [suggestions, setSuggestions] = useState([])
  const [searching, setSearching] = useState(false)
  const debounce = useRef(null)
  const ids = (params.get('ids') || '').split(',').filter(Boolean)

  useEffect(() => {
    if (!ids.length) { setPrograms([]); return }
    setLoading(true)
    api.get('/programs/compare', { params: { ids: ids.join(',') } })
      .then(({ data }) => setPrograms(data.items || data.programs || data || []))
      .catch(async () => {
        const res = await Promise.allSettled(ids.map((id) => api.get(`/programs/${id}`)))
        setPrograms(res.filter((r) => r.status === 'fulfilled').map((r) => r.value.data))
      })
      .finally(() => setLoading(false))
  }, [params]) // eslint-disable-line

  const setIds = (next) => {
    setParams(next.length ? { ids: next.join(',') } : {})
    localStorage.setItem('compare', JSON.stringify(next.map(Number)))
  }
  const add = (id) => {
    if (!ids.includes(String(id)) && ids.length < MAX_COMPARE) setIds([...ids, String(id)])
    setQuery(''); setSuggestions([])
  }
  const remove = (id) => setIds(ids.filter((x) => x !== String(id)))
  const clearAll = () => { setIds([]); localStorage.removeItem('compare') }

  const onSearch = (value) => {
    setQuery(value)
    clearTimeout(debounce.current)
    if (value.trim().length < 2) { setSuggestions([]); return }
    debounce.current = setTimeout(() => {
      setSearching(true)
      api.get('/programs', { params: { search: value.trim(), page: 1, page_size: 8 } })
        .then(({ data }) => setSuggestions((data.items || []).filter((p) => !ids.includes(String(p.id)))))
        .catch(() => setSuggestions([]))
        .finally(() => setSearching(false))
    }, 250)
  }

  const rows = [
    ['Level', (p) => p.level], ['Group', (p) => p.group || '—'], ['Shift', (p) => p.shift || '—'],
    ['Department', (p) => p.department], ['Faculty', (p) => p.faculty],
    ['Duration', (p) => (p.duration_years ? `${p.duration_years} years` : '—')],
    ['Tuition Fee', (p) => formatPKR(p.fee?.tuition_fee)], ['Other Dues', (p) => formatPKR(p.fee?.other_dues)],
    ['1st Semester Total', (p) => formatPKR(p.fee?.total_first_semester)],
    ['Next Semesters (each)', (p) => formatPKR(p.fee?.total_next_semesters)],
    ['Min. Marks', (p) => (p.requirement?.min_marks_pct != null ? `${p.requirement.min_marks_pct}%` : 'Not specified')],
    ['Seats', (p) => p.requirement?.seats ?? 'Not specified'],
    ['Entry Test', (p) => p.requirement?.entry_test || 'Not specified'],
  ]

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <h1 className="text-3xl font-extrabold text-navy dark:text-white">Compare Programs</h1>
      <p className="mt-1 text-slate-500">Search and add up to {MAX_COMPARE} programs to compare fees, eligibility and duration side by side. Remove any program with the ✕ button.</p>

      {/* Search & add */}
      <div className="relative mt-6 max-w-xl">
        <input
          value={query}
          onChange={(e) => onSearch(e.target.value)}
          disabled={ids.length >= MAX_COMPARE}
          placeholder={ids.length >= MAX_COMPARE ? `Maximum ${MAX_COMPARE} programs selected — remove one to add another` : 'Type a program name… e.g. BS Computer Science'}
          className="w-full rounded-xl border border-slate-300 dark:border-white/20 bg-white dark:bg-white/5 px-4 py-3 text-sm shadow-sm focus:border-gold focus:outline-none disabled:opacity-60"
        />
        {(suggestions.length > 0 || searching) && (
          <ul className="absolute inset-x-0 top-full z-20 mt-2 overflow-hidden rounded-xl border border-slate-200 dark:border-white/10 bg-white dark:bg-navy shadow-xl">
            {searching && <li className="px-4 py-3 text-sm text-slate-500">Searching…</li>}
            {suggestions.map((p) => (
              <li key={p.id}>
                <button onClick={() => add(p.id)} className="flex w-full items-center justify-between gap-3 px-4 py-3 text-start text-sm hover:bg-gold/10">
                  <span><span className="font-semibold text-navy dark:text-white">{p.name}</span>
                    <span className="block text-xs text-slate-500">{p.department} · {p.level}{p.group ? ` · ${p.group}` : ''}</span></span>
                  <span className={btnGoldSm}>+ Add</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Selected chips with remove */}
      {programs.length > 0 && (
        <div className="mt-4 flex flex-wrap items-center gap-2">
          {programs.map((p) => (
            <span key={p.id} className="inline-flex items-center gap-2 rounded-full bg-navy py-1.5 ps-4 pe-2 text-sm font-semibold text-white">
              {p.name}
              <button onClick={() => remove(p.id)} title={`Remove ${p.name}`} className="flex h-6 w-6 items-center justify-center rounded-full bg-white/15 text-white transition hover:bg-red-500">✕</button>
            </span>
          ))}
          <button onClick={clearAll} className={btnOutlineSm}>Clear all</button>
        </div>
      )}

      <div className="mt-6">
        {loading ? <Skeleton className="h-64" /> : programs.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-300 p-10 text-center text-slate-500">
            No programs selected yet. Search above to add programs, or use “Compare” on the <Link to="/programs" className="underline font-semibold">Programs page</Link>.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-white/10 bg-white dark:bg-white/5">
            <table className="w-full min-w-[640px] text-sm">
              <thead>
                <tr className="bg-navy text-white">
                  <th className="px-4 py-3 text-start">Feature</th>
                  {programs.map((p) => (
                    <th key={p.id} className="px-4 py-3 text-start">
                      <span className="flex items-start justify-between gap-2">
                        <span>{p.name}
                          <Link to={`/programs/${p.id}`} className="block text-xs font-normal text-gold-light underline">View details</Link>
                        </span>
                        <button onClick={() => remove(p.id)} title={`Remove ${p.name} from comparison`} className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-white/15 text-xs text-white transition hover:bg-red-500">✕</button>
                      </span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map(([label, fn], i) => (
                  <tr key={label} className={i % 2 ? 'bg-slate-50 dark:bg-white/5' : ''}>
                    <td className="px-4 py-2.5 font-semibold text-slate-500">{label}</td>
                    {programs.map((p) => <td key={p.id} className="px-4 py-2.5 font-medium">{fn(p)}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      <p className="mt-3 text-xs text-slate-500">Fees: Revised Fee Structure Fall 2025, new intake only. Please verify with the official office.</p>
    </div>
  )
}
