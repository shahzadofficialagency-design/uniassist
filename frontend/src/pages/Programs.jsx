import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import api, { errorMessage } from '../api/client'
import ProgramCard from '../components/ProgramCard'
import { btnGoldSm, btnOutlineSm } from '../components/ui'
import { PageSkeleton } from '../components/Skeleton'
import { useLanguage } from '../context/LanguageContext'

export default function Programs() {
  const { t } = useLanguage()
  const [params, setParams] = useSearchParams()
  const navigate = useNavigate()
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [faculties, setFaculties] = useState([])
  const [departments, setDepartments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [compareIds, setCompareIds] = useState(() => JSON.parse(localStorage.getItem('compare') || '[]'))

  const search = params.get('search') || ''
  const facultyId = params.get('faculty_id') || ''
  const deptId = params.get('department_id') || ''
  const level = params.get('level') || ''
  const group = params.get('group') || ''
  const page = Number(params.get('page') || 1)
  const pageSize = 12

  useEffect(() => { api.get('/faculties').then(({ data }) => setFaculties(data.items || data || [])).catch(() => {}) }, [])
  useEffect(() => {
    api.get('/departments', { params: { faculty_id: facultyId || undefined } }).then(({ data }) => setDepartments(data.items || data || [])).catch(() => setDepartments([]))
  }, [facultyId])

  useEffect(() => {
    setLoading(true); setError('')
    api.get('/programs', { params: { search: search || undefined, faculty_id: facultyId || undefined, department_id: deptId || undefined, level: level || undefined, group: group || undefined, page, page_size: pageSize } })
      .then(({ data }) => { setItems(data.items || []); setTotal(data.total ?? (data.items || []).length) })
      .catch((e) => setError(errorMessage(e, 'Could not load programs. Is the backend running?')))
      .finally(() => setLoading(false))
  }, [search, facultyId, deptId, level, group, page])

  const setParam = (k, v) => {
    const next = new URLSearchParams(params)
    if (v) next.set(k, v); else next.delete(k)
    if (k !== 'page') next.set('page', '1')
    setParams(next)
  }

  const toggleCompare = (program) => {
    setCompareIds((prev) => {
      const next = prev.includes(program.id) ? prev.filter((id) => id !== program.id) : [...prev.slice(-2), program.id]
      localStorage.setItem('compare', JSON.stringify(next))
      return next
    })
  }

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / pageSize)), [total])
  const input = 'rounded-lg border border-slate-300 dark:border-white/20 bg-white dark:bg-white/5 px-3 py-2.5 text-sm w-full'

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <h1 className="text-3xl font-extrabold text-navy dark:text-white">{t('programs')}</h1>
      <p className="mt-1 text-slate-500">{total} programs · Fall 2025 fee structure (new intake only) · {t('verifyNote')}</p>

      <div className="mt-5 grid gap-3 md:grid-cols-5">
        <input value={search} onChange={(e) => setParam('search', e.target.value)} placeholder={t('searchPlaceholder')} className={`${input} md:col-span-2`} />
        <select value={facultyId} onChange={(e) => { setParam('faculty_id', e.target.value); setParam('department_id', '') }} className={input}>
          <option value="">{t('faculty')}: {t('all')}</option>
          {faculties.map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}
        </select>
        <select value={deptId} onChange={(e) => setParam('department_id', e.target.value)} className={input}>
          <option value="">{t('department')}: {t('all')}</option>
          {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
        <div className="flex gap-2">
          <select value={level} onChange={(e) => setParam('level', e.target.value)} className={input}>
            <option value="">{t('level')}: {t('all')}</option>
            <option value="BS">BS / Undergraduate</option><option value="MS">MS / MPhil</option><option value="PhD">PhD</option><option value="Diploma">Diploma</option>
          </select>
          <select value={group} onChange={(e) => setParam('group', e.target.value)} className={input}>
            <option value="">{t('group')}: {t('all')}</option>
            <option value="Group-A">Group-A</option><option value="Group-B">Group-B</option>
          </select>
        </div>
      </div>

      {compareIds.length > 0 && (
        <div className="mt-4 flex flex-wrap items-center gap-3 rounded-xl bg-navy px-4 py-3 text-white">
          <span className="text-sm font-semibold">{compareIds.length} selected for comparison</span>
          <button onClick={() => navigate(`/compare?ids=${compareIds.join(',')}`)} className={btnGoldSm}>Compare Now →</button>
          <button onClick={() => { setCompareIds([]); localStorage.removeItem('compare') }} className="text-sm font-semibold text-white/80 underline underline-offset-2 hover:text-white">Clear</button>
        </div>
      )}

      <div className="mt-6">
        {loading ? <PageSkeleton /> : error ? (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-700">{error}</div>
        ) : items.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-300 p-10 text-center text-slate-500">{t('noResults')} Try a different search or filter.</div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((p) => <ProgramCard key={p.id} program={p} onCompare={toggleCompare} compared={compareIds.includes(p.id)} />)}
          </div>
        )}
      </div>

      <div className="mt-8 flex items-center justify-center gap-3">
        <button disabled={page <= 1} onClick={() => setParam('page', String(page - 1))} className={btnOutlineSm}>← Previous</button>
        <span className="text-sm text-slate-500">Page {page} of {totalPages}</span>
        <button disabled={page >= totalPages} onClick={() => setParam('page', String(page + 1))} className={btnOutlineSm}>Next →</button>
      </div>
    </div>
  )
}
