import { useEffect, useMemo, useState } from 'react'
import api from '../api/client'
import Reveal from '../components/Reveal'
import Skeleton from '../components/Skeleton'

const DIRECTION_LABEL = {
  'AC to BJC': 'Abbasia Campus → Baghdad Campus',
  'BJC to AC': 'Baghdad Campus → Abbasia Campus',
  'AC to KH. FC': 'Abbasia Campus → Khwaja Fareed Campus',
  'KH. FC to AC': 'Khwaja Fareed Campus → Abbasia Campus',
}

export default function Transport() {
  const [data, setData] = useState(null)
  const [direction, setDirection] = useState('All')

  useEffect(() => {
    api.get('/transport').then(({ data }) => setData(data)).catch(() => setData({ sections: [] }))
  }, [])

  const directions = data?.directions || []
  const sections = useMemo(() => (data?.sections || []).map((s) => ({
    ...s,
    trips: direction === 'All' ? s.trips : s.trips.filter((t) => t.direction === direction),
  })).filter((s) => s.trips.length > 0), [data, direction])

  if (!data) return <div className="mx-auto max-w-7xl px-4 py-10"><Skeleton rows={6} /></div>

  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl font-extrabold text-navy dark:text-white">University Transport</h1>
          <p className="mt-1 text-slate-500">Bus point timings & route numbers between Abbasia, Baghdad-ul-Jadeed and Khwaja Fareed campuses.</p>
        </div>
        <span className="rounded-full bg-gold/15 border border-gold/50 px-3 py-1.5 text-xs font-bold text-navy dark:text-gold">
          Official schedule · Effective {data.effective_from}
        </span>
      </div>

      <div className="mt-5 flex flex-wrap gap-2">
        {['All', ...directions].map((d) => (
          <button key={d} onClick={() => setDirection(d)}
            className={`rounded-full px-3.5 py-1.5 text-sm font-semibold border transition ${direction === d ? 'bg-navy text-white border-navy dark:bg-gold dark:text-navy dark:border-gold' : 'border-slate-300 dark:border-white/20 hover:border-gold'}`}>
            {d === 'All' ? 'All directions' : DIRECTION_LABEL[d]}
          </button>
        ))}
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        {sections.map((s, si) => (
          <Reveal key={s.name} delay={(si % 2) * 110} className="h-full">
            <section className="h-full overflow-hidden rounded-2xl border border-slate-200 dark:border-white/10 bg-white dark:bg-white/5">
              <header className="flex items-center justify-between bg-navy px-5 py-3">
                <h2 className="font-extrabold text-white">🚌 {s.name}</h2>
                <span className="text-xs font-semibold text-white/75">{s.days}</span>
              </header>
              <div className="divide-y divide-slate-100 dark:divide-white/5">
                {directions.filter((d) => direction === 'All' || d === direction).map((d) => {
                  const rows = s.trips.filter((t) => t.direction === d)
                  if (!rows.length) return null
                  return (
                    <div key={d} className="px-5 py-3">
                      <p className="text-sm font-bold text-navy dark:text-gold">{DIRECTION_LABEL[d]}</p>
                      <ul className="mt-1.5 space-y-1.5">
                        {rows.map((t) => (
                          <li key={t.time + t.routes} className="flex gap-3 text-sm">
                            <span className="shrink-0 rounded-md bg-gold/15 px-2 py-0.5 font-bold text-navy dark:text-gold">{t.time}</span>
                            <span className="text-slate-600 dark:text-slate-300 break-words">Routes {t.routes}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )
                })}
              </div>
            </section>
          </Reveal>
        ))}
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-3">
        <Reveal className="h-full">
          <div className="h-full rounded-2xl border border-slate-200 dark:border-white/10 bg-white dark:bg-white/5 p-5">
            <h3 className="font-extrabold text-navy dark:text-white">🔑 Route indication keys</h3>
            <ul className="mt-2 space-y-1 text-sm text-slate-600 dark:text-slate-300">
              {Object.entries(data.route_keys || {}).map(([k, v]) => (
                <li key={k}><b className="text-navy dark:text-gold">{k}</b> — {v}</li>
              ))}
              {Object.entries(data.campuses || {}).map(([k, v]) => (
                <li key={k}><b className="text-navy dark:text-gold">{k}</b> — {v}</li>
              ))}
            </ul>
          </div>
        </Reveal>
        <Reveal delay={110} className="h-full">
          <div className="h-full rounded-2xl border border-slate-200 dark:border-white/10 bg-white dark:bg-white/5 p-5">
            <h3 className="font-extrabold text-navy dark:text-white">📞 Transport information</h3>
            <ul className="mt-2 space-y-1.5 text-sm text-slate-600 dark:text-slate-300">
              {(data.contacts || []).map((c) => (
                <li key={c.phone}><b>{c.shift} shift</b> — {c.for_route}: <b className="text-navy dark:text-gold">{c.phone}</b></li>
              ))}
              <li>Complaints (WhatsApp): <b className="text-navy dark:text-gold">{data.complaint_whatsapp}</b></li>
            </ul>
          </div>
        </Reveal>
        <Reveal delay={220} className="h-full">
          <div className="h-full rounded-2xl border border-amber-300/60 bg-amber-50 dark:bg-amber-900/10 p-5">
            <h3 className="font-extrabold text-navy dark:text-amber-200">⚠️ Note</h3>
            <ul className="mt-2 list-disc space-y-1 ps-5 text-sm text-amber-800 dark:text-amber-200/90">
              {(data.notes || []).map((n) => <li key={n}>{n}</li>)}
            </ul>
          </div>
        </Reveal>
      </div>

      <Reveal>
        <figure className="mt-6 overflow-hidden rounded-2xl border border-slate-200 dark:border-white/10 bg-white dark:bg-white/5">
          <a href="/images/transport-schedule.jpg" target="_blank" rel="noreferrer">
            <img src="/images/transport-schedule.jpg" alt="Official IUB Transport Schedule notice (w.e.f. 16-11-2026)" loading="lazy" className="mx-auto max-h-[560px] w-auto object-contain" />
          </a>
          <figcaption className="px-5 py-3 text-sm text-slate-500">
            Official notice — Transport Schedule of The Islamia University of Bahawalpur, w.e.f. 16-11-2026 (Principal Transport Officer). Tap the image to view it full size and cross-check any timing.
          </figcaption>
        </figure>
      </Reveal>
    </div>
  )
}
