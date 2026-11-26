import { formatPKR } from '../api/client'

export default function FeeTable({ fee, compact = false }) {
  if (!fee) {
    return <p className="text-sm text-slate-500">Fee information is not available for this program yet. Please verify with the official office.</p>
  }
  const rows = [
    ['Tuition Fee', fee.tuition_fee],
    ['Other Dues', fee.other_dues],
    ['Total — 1st Semester', fee.total_first_semester],
    ['Total — Next Semesters (each)', fee.total_next_semesters],
  ].filter(([, v]) => v !== null && v !== undefined)

  return (
    <div className={`overflow-hidden rounded-xl border border-slate-200 dark:border-white/10 ${compact ? 'text-sm' : ''}`}>
      <table className="w-full text-left">
        <thead>
          <tr className="bg-navy text-white text-xs uppercase tracking-wide">
            <th className="px-4 py-2.5 font-semibold">Charge</th>
            <th className="px-4 py-2.5 font-semibold text-right">Amount {fee.currency ? `(${fee.currency})` : '(PKR)'}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(([label, value], i) => (
            <tr key={label} className={i % 2 ? 'bg-slate-50 dark:bg-white/5' : 'bg-white dark:bg-transparent'}>
              <td className="px-4 py-2.5 font-medium">{label}</td>
              <td className="px-4 py-2.5 text-right font-semibold text-navy dark:text-gold-light">{formatPKR(value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {(fee.session || fee.intake) && (
        <p className="px-4 py-2 text-xs text-slate-500 bg-gold-light/20">
          {fee.session ? `Session: ${fee.session}` : ''}{fee.session && fee.intake ? ' · ' : ''}{fee.intake || ''}
        </p>
      )}
    </div>
  )
}
