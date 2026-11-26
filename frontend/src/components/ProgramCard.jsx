import { Link } from 'react-router-dom'
import { formatPKR } from '../api/client'
import { btnGoldSm, btnOutlineSm, btnPrimarySm } from './ui'
import { useLanguage } from '../context/LanguageContext'

export default function ProgramCard({ program, onCompare, compared }) {
  const { t } = useLanguage()
  const fee = program.fee || {}
  return (
    <article className="flex flex-col rounded-2xl border border-slate-200 dark:border-white/10 bg-white dark:bg-white/5 p-5 shadow-sm hover:shadow-md transition">
      <div className="flex items-start justify-between gap-2">
        <span className="rounded-full bg-navy/5 dark:bg-white/10 px-2.5 py-1 text-xs font-semibold text-navy dark:text-gold-light">{program.level || 'Program'}</span>
        {program.group && <span className="rounded-full bg-gold/15 px-2.5 py-1 text-xs font-semibold text-navy dark:text-gold">{program.group}</span>}
      </div>
      <h3 className="mt-3 font-bold text-navy dark:text-white leading-snug">{program.name}</h3>
      <p className="mt-1 text-sm text-slate-500">{program.department || ''}{program.faculty ? ` · ${program.faculty}` : ''}</p>
      <dl className="mt-4 grid grid-cols-2 gap-2 text-sm">
        <div className="rounded-lg bg-bg dark:bg-white/5 p-2.5">
          <dt className="text-xs text-slate-500">{t('firstSemester')}</dt>
          <dd className="font-bold text-navy dark:text-white">{formatPKR(fee.total_first_semester)}</dd>
        </div>
        <div className="rounded-lg bg-bg dark:bg-white/5 p-2.5">
          <dt className="text-xs text-slate-500">{t('nextSemesters')}</dt>
          <dd className="font-bold text-navy dark:text-white">{formatPKR(fee.total_next_semesters)}</dd>
        </div>
      </dl>
      <p className="mt-3 text-xs text-slate-500">
        {program.duration_years ? `${t('duration')}: ${program.duration_years} ${t('years')}` : ''}
        {program.shift ? ` · ${t('shift')}: ${program.shift}` : ''}
        {program.requirement?.seats ? ` · ${t('seats')}: ${program.requirement.seats}` : ''}
      </p>
      <div className="mt-auto pt-4 flex gap-2">
        <Link to={`/programs/${program.id}`} className={`${btnPrimarySm} flex-1`}>{t('viewDetails')}</Link>
        {onCompare && (
          <button onClick={() => onCompare(program)} className={compared ? btnGoldSm : btnOutlineSm}>
            {compared ? '✓ Added' : t('addToCompare')}
          </button>
        )}
      </div>
    </article>
  )
}
