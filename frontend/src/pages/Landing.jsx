import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'
import Reveal, { tiltProps } from '../components/Reveal'
import Skeleton from '../components/Skeleton'
import { useLanguage } from '../context/LanguageContext'

function fmtDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })
}

// Dean names & portraits: official IUB website (iub.edu.pk), fetched Nov 2026.
const DEANS = {
  'faculty-of-agriculture-environment': 'Prof. Dr. Tanveer Hussain Turabi',
  'faculty-of-arts-and-languages': 'Prof. Dr. Syed Amir Sohail',
  'faculty-of-chemical-biological-sciences': 'Prof. Dr. Muhammad Saleem',
  'faculty-of-computing': 'Prof. Dr. Dost Muhammad Khan',
  'faculty-of-education': 'Prof. Dr. Irshad Hussain',
  'faculty-of-engineering': 'Prof. Dr. Muhammad Amjad',
  'faculty-of-islamic-arabic-studies': 'Prof. Dr. Sheikh Shafiq-ur-Rehman',
  'faculty-of-law': 'Prof. Dr. Rao Imran Habib',
  'faculty-of-management-sciences-commerce': 'Prof. Dr. Jawad Iqbal',
  'faculty-of-medicine-allied-health-sciences': 'Prof. Dr. Qaiser Jabeen',
  'faculty-of-pharmacy': 'Prof. Dr. Qaiser Jabeen',
  'faculty-of-physical-mathematical-sciences': 'Prof. Dr. Ghulam Mustafa',
  'faculty-of-social-sciences': 'Prof. Dr. Rubina Bhatti',
  'faculty-of-veterinary-animal-sciences': 'Prof. Dr. Muhammad Khalid Mansoor',
}

function FacultyCard({ f }) {
  const [imgOk, setImgOk] = useState(true)
  const dean = DEANS[f.slug]
  return (
    <Link to={`/programs?faculty_id=${f.id || ''}`} {...tiltProps(6)} className="tilt3d group block h-full overflow-hidden rounded-2xl border border-slate-200 dark:border-white/10 bg-white dark:bg-white/5 hover:border-gold hover:shadow-lg">
      <div className="relative h-48 overflow-hidden bg-gradient-to-br from-navy to-[#241a5e]">
        {imgOk && f.slug && (
          <img src={`/images/faculties/${f.slug}.jpg`} alt={dean ? `Dean — ${f.name}` : f.name} loading="lazy"
            onError={() => setImgOk(false)}
            className="h-full w-full object-cover object-center group-hover:scale-105 transition duration-500" />
        )}
        <span className="absolute bottom-2 start-2 rounded-full bg-navy/85 px-2.5 py-0.5 text-[11px] font-bold text-gold-light backdrop-blur">
          {f.programs ?? 0} programs · {f.departments ?? 0} departments
        </span>
      </div>
      <div className="p-4">
        <p className="font-bold text-navy dark:text-white group-hover:text-gold transition">{f.name}</p>
        {dean && <p className="mt-0.5 text-xs text-slate-500">Dean: {dean}</p>}
        <p className="mt-2 text-sm font-semibold text-gold">View programs →</p>
      </div>
    </Link>
  )
}

export default function Landing() {
  const { t } = useLanguage()
  const [faculties, setFaculties] = useState([])
  const [announcements, setAnnouncements] = useState([])
  const [deadlines, setDeadlines] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.allSettled([api.get('/faculties'), api.get('/announcements'), api.get('/deadlines')]).then(([f, a, d]) => {
      if (f.status === 'fulfilled') setFaculties(f.value.data?.items || f.value.data || [])
      if (a.status === 'fulfilled') setAnnouncements(a.value.data?.items || a.value.data || [])
      if (d.status === 'fulfilled') setDeadlines(d.value.data?.items || d.value.data || [])
      setLoading(false)
    })
  }, [])

  const today = new Date().toISOString().slice(0, 10)

  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden bg-navy">
        <div className="absolute inset-0 bg-gradient-to-br from-navy via-[#241a5e] to-navy" />
        <div className="absolute -top-24 -end-24 h-72 w-72 rounded-full bg-gold/20 blur-3xl" />
        <div className="absolute -bottom-32 -start-16 h-72 w-72 rounded-full bg-gold/10 blur-3xl" />
        <div className="relative mx-auto max-w-7xl px-4 pt-14 pb-10 sm:pt-20 text-white">
          <div className="flex items-center gap-3">
            <span className="grid h-14 w-14 place-items-center rounded-full bg-white overflow-hidden ring-2 ring-gold/70"><img src="/assets/iub-logo.jpg" alt="IUB" className="h-12 w-12 object-contain" /></span>
            <div>
              <p className="text-sm font-semibold text-gold-light">The Islamia University of Bahawalpur</p>
              <p className="text-xs text-white/60">Est. 1925 · Bahawalpur, Punjab, Pakistan</p>
            </div>
          </div>
          <h1 className="mt-6 max-w-2xl text-4xl sm:text-5xl font-extrabold leading-tight">{t('welcome')}</h1>
          <p className="mt-3 max-w-xl text-white/85">{t('tagline')}</p>
          <p className="mt-2 max-w-xl text-sm text-white/70">457 programs · 14 faculties · 104 departments — fees from the official Revised Fee Structure Fall 2025, eligibility &amp; deadlines from the official IUB website.</p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Link to="/programs" className="rounded-full bg-gold px-6 py-3 font-bold text-navy shadow-lg shadow-gold/20 hover:bg-gold-light transition">{t('explorePrograms')}</Link>
            <Link to="/chat" className="rounded-full border border-white/40 px-6 py-3 font-bold text-white hover:bg-white/10 transition">{t('askChatbot')} →</Link>
          </div>
          <div className="mt-8 flex flex-wrap gap-2 text-sm">
            {['BS AI ki fee kitni hai?', 'Admission ki last date kia hai?', 'BS AI ke liye kitne marks chahiye?', 'بی ایس کمپیوٹر سائنس کی فیس؟'].map((q) => (
              <Link key={q} to="/chat" state={{ prefill: q }} className="rounded-full bg-white/10 px-3.5 py-1.5 hover:bg-white/20 transition">{q}</Link>
            ))}
          </div>
        </div>
        <div className="relative mx-auto max-w-7xl px-4 pb-10">
          <img src="/images/iub-centenary.jpg" alt="100 Years of Legacy — The Islamia University of Bahawalpur" className="float-slow w-full rounded-2xl border border-white/15 shadow-2xl object-cover" />
          <p className="mt-2 text-end text-[11px] text-white/50">Photo: The Islamia University of Bahawalpur (iub.edu.pk)</p>
        </div>
      </section>

      {/* Stats */}
      <section className="mx-auto max-w-7xl px-4 py-8">
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {[['457', t('statsPrograms')], ['14', t('statsFaculties')], ['104', t('statsDepts')], ['4', 'Languages — EN · اردو · Roman Urdu · Mixed']].map(([n, l], i) => (
            <Reveal key={l} delay={i * 90} className="h-full">
              <div className="h-full rounded-2xl bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 p-4 text-center hover:border-gold/60 hover:shadow transition">
                <p className="text-2xl sm:text-3xl font-extrabold text-navy dark:text-gold">{n}</p>
                <p className="text-xs sm:text-sm text-slate-500">{l}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* Faculties */}
      <section className="mx-auto max-w-7xl px-4 py-4">
        <h2 className="text-2xl font-extrabold text-navy dark:text-white">{t('featured')}</h2>
        {loading ? (
          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{[1, 2, 3, 4, 5, 6].map((i) => <Skeleton key={i} className="h-20" />)}</div>
        ) : faculties.length === 0 ? (
          <p className="mt-4 text-slate-500">{t('noResults')} Backend data will appear here once the API is running.</p>
        ) : (
          <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {faculties.map((f, i) => (
              <Reveal key={f.id || f.name} delay={(i % 3) * 110} className="h-full">
                <FacultyCard f={f} />
              </Reveal>
            ))}
          </div>
        )}
        <p className="mt-2 text-end text-[11px] text-slate-400">Dean photos &amp; names: The Islamia University of Bahawalpur — iub.edu.pk</p>
      </section>

      {/* Canteens */}
      <section className="mx-auto max-w-7xl px-4 py-4">
        <div className="flex flex-wrap items-end justify-between gap-2">
          <h2 className="text-2xl font-extrabold text-navy dark:text-white">Campus Canteens</h2>
          <Link to="/canteen" className="text-sm font-bold text-gold hover:underline">Full rate list 2026-27 →</Link>
        </div>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          {[['/images/heritage-cafe.jpg', 'Heritage Cafe', 'The colourful student cafe at Baghdad-ul-Jadeed Campus — a favourite hangout between classes.'],
            ['/images/main-canteen.jpg', 'Main Canteen IUB', 'The main canteen serving breakfast, lunch, snacks and drinks at official university rates.']].map(([src, name, desc], i) => (
            <Reveal key={src} delay={i * 120} className="h-full">
              <Link to="/canteen" {...tiltProps(5)} className="tilt3d group block h-full overflow-hidden rounded-2xl border border-slate-200 dark:border-white/10">
                <div className="relative h-56 overflow-hidden">
                  <img src={src} alt={name} loading="lazy" className="h-full w-full object-cover group-hover:scale-105 transition duration-500" />
                  <span className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-navy/90 to-transparent px-4 pb-3 pt-10 text-white">
                    <span className="block font-extrabold">{name}</span>
                    <span className="block text-xs text-white/80">{desc}</span>
                  </span>
                </div>
              </Link>
            </Reveal>
          ))}
        </div>
        <div className="mt-4 flex flex-wrap gap-2 text-sm">
          {[['Chicken Burger', 'Rs 140'], ['Chicken Biryani + Raita', 'Rs 160/90'], ['Tea (Mix Chai)', 'Rs 60'], ['Chicken Shwarma (Large)', 'Rs 120'], ['Halwa Puri + Chanay', 'Rs 130']].map(([item, price]) => (
            <span key={item} className="rounded-full border border-gold/50 bg-gold/5 px-3 py-1.5">{item} · <b className="text-navy dark:text-gold">{price}</b></span>
          ))}
          <Link to="/chat" state={{ prefill: 'Canteen mein chicken burger kitne ka hai?' }} className="rounded-full bg-navy px-3 py-1.5 font-semibold text-white">Ask the chatbot a price →</Link>
        </div>
      </section>

      {/* University transport strip */}
      <section className="mx-auto max-w-7xl px-4 pb-2">
        <Reveal>
          <Link to="/transport" className="group flex flex-wrap items-center gap-4 overflow-hidden rounded-2xl bg-navy px-6 py-5 shadow-lg">
            <span className="text-4xl">🚌</span>
            <span className="min-w-52 flex-1">
              <span className="block text-lg font-extrabold text-white">University Transport — Bus Points</span>
              <span className="block text-sm text-white/75">Abbasia ⇄ Baghdad-ul-Jadeed ⇄ Khwaja Fareed · First point 7:00 AM · Last point 6:45 PM · Saturday service on routes 31 & 32S–38</span>
            </span>
            <span className="flex flex-wrap gap-2 text-xs font-bold">
              <span className="rounded-full bg-white/10 px-3 py-1.5 text-goldlight">Morning 7:30 AM</span>
              <span className="rounded-full bg-white/10 px-3 py-1.5 text-goldlight">Afternoon 12:30 PM</span>
              <span className="rounded-full bg-white/10 px-3 py-1.5 text-goldlight">Evening 4:30 PM</span>
            </span>
            <span className="rounded-lg bg-gold px-4 py-2 text-sm font-bold text-navy group-hover:scale-105 transition">Full schedule →</span>
          </Link>
        </Reveal>
      </section>

      {/* Deadlines + Announcements */}
      <section className="mx-auto grid max-w-7xl gap-6 px-4 py-8 lg:grid-cols-2">
        <Reveal className="h-full min-w-0">
        <div className="h-full rounded-2xl bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-extrabold text-navy dark:text-white">📅 Admission Deadlines</h2>
            <span className="text-[11px] font-semibold text-slate-400">Source: iub.edu.pk</span>
          </div>
          {deadlines.length === 0 ? (
            <p className="mt-3 text-sm text-slate-500">No deadlines published right now. The next intake advertisement will appear here.</p>
          ) : (
            <ul className="mt-4 space-y-3">
              {deadlines.map((d) => {
                const passed = d.closes_on && d.closes_on < today
                return (
                  <li key={d.id} className="rounded-xl border border-slate-200 dark:border-white/10 p-4 hover:border-gold/60 transition">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-bold text-navy dark:text-white">{d.title}</p>
                      <span className={`rounded-full px-2.5 py-0.5 text-[11px] font-bold ${passed ? 'bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-300' : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300'}`}>{passed ? 'Last date passed' : 'Open'}</span>
                    </div>
                    <p className="mt-1 text-sm"><span className="text-slate-500">Last date:</span> <span className="font-extrabold text-gold">{fmtDate(d.closes_on)}</span> <span className="text-slate-400">· {d.session}</span></p>
                    {d.description && <p className="mt-1 text-sm text-slate-500">{d.description}</p>}
                  </li>
                )
              })}
            </ul>
          )}
          <div className="mt-5 flex flex-wrap gap-2">
            <Link to="/fee-calculator" className="rounded-lg bg-navy px-4 py-2 text-sm font-semibold text-white">{t('feeCalculator')}</Link>
            <Link to="/eligibility" className="rounded-lg border border-navy/20 dark:border-white/20 px-4 py-2 text-sm font-semibold">{t('eligibility')}</Link>
          </div>
        </div>
        </Reveal>
        <Reveal delay={120} className="h-full min-w-0">
        <div className="h-full rounded-2xl bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 p-6">
          <h2 className="text-xl font-extrabold text-navy dark:text-white">{t('announcements')}</h2>
          {announcements.length === 0 ? (
            <p className="mt-3 text-sm text-slate-500">No announcements right now. Fee structure currently published: Fall 2025, new intake only.</p>
          ) : (
            <ul className="mt-3 space-y-3">
              {announcements.map((a) => (
                <li key={a.id} className="border-s-4 border-gold ps-3">
                  <p className="font-semibold break-words">{a.title}</p>
                  <p className="text-sm text-slate-500 break-words">{a.body}</p>
                </li>
              ))}
            </ul>
          )}
        </div>
        </Reveal>
      </section>

      {/* Campus gallery */}
      <section className="mx-auto max-w-7xl px-4 py-4">
        <h2 className="text-2xl font-extrabold text-navy dark:text-white">Campus Life</h2>
        <div className="mt-5 grid gap-4 sm:grid-cols-3">
          {[['/images/iub-campus-life.jpg', 'Student cultural activities — main campus courtyard'],
            ['/images/iub-convocation.jpg', 'Convocation — graduating students'],
            ['/images/iub-labs.jpg', 'Laboratories & classroom learning'],
            ['/images/heritage-cafe-2.jpg', 'Heritage Cafe — evening view'],
            ['/images/faculty-computing.jpg', 'Faculty of Computing — main entrance'],
            ['/images/main-canteen-2.jpg', 'Main Canteen — side view'],
            ['/images/abbasia-campus.jpg', 'Abbasia Campus — the historic campus at University Chowk'],
            ['/images/amphitheater.jpg', 'University amphitheater — Baghdad-ul-Jadeed Campus'],
            ['/images/library.jpg', 'Sir Sadiq Muhammad Khan Library — ground floor']].map(([src, cap], i) => (
            <Reveal key={src} delay={(i % 3) * 110} className="h-full">
              <figure className="group h-full overflow-hidden rounded-2xl border border-slate-200 dark:border-white/10">
                <img src={src} alt={cap} className="h-44 w-full object-cover group-hover:scale-105 transition duration-500" loading="lazy" />
                <figcaption className="bg-white dark:bg-white/5 px-4 py-2.5 text-sm text-slate-600 dark:text-slate-300">{cap}</figcaption>
              </figure>
            </Reveal>
          ))}
        </div>
        <p className="mt-2 text-end text-[11px] text-slate-400">Photos: The Islamia University of Bahawalpur — iub.edu.pk</p>
      </section>

      {/* About */}
      <section className="mx-auto max-w-7xl px-4 py-8">
        <div className="overflow-hidden rounded-2xl border border-slate-200 dark:border-white/10 grid lg:grid-cols-2">
          <img src="/assets/iub-campus.jpg" alt="IUB Main Building" className="h-56 w-full object-cover lg:h-full" />
          <div className="bg-white dark:bg-white/5 p-6 sm:p-8">
            <h2 className="text-xl font-extrabold text-navy dark:text-white">About IUB</h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
              Founded in 1925 as Jamia Abbasia by Nawab Sir Sadiq Muhammad Khan Abbasi-V and chartered as a university in 1975, The Islamia University of Bahawalpur is a public-sector university in southern Punjab with <b>7 campuses</b>, <b>135 departments</b> and <b>300+ disciplines</b> serving around <b>58,000 students</b>. It was placed in the <b>800+ band of the Times Higher Education World University Rankings 2025</b>. Its vision is to be a world-class university with a global outlook and a catalyst for socioeconomic transformation of the region. The Vice Chancellor is <b>Prof. Dr. Muhammad Kamran</b>.
              UniAssist helps applicants explore its programs, official fees, eligibility criteria and admission deadlines in English, Urdu script and Roman Urdu — without visiting the campus.
            </p>
            <p className="mt-2 text-[11px] text-slate-400">Source: iub.edu.pk — About University</p>
            <p className="mt-3 text-xs text-slate-500">{t('verifyNote')} Group-A / Group-B labels are shown exactly as printed in the official fee PDF. Eligibility criteria and deadlines are taken from the official IUB website (iub.edu.pk).</p>
            <div className="mt-4 flex flex-wrap gap-2">
              <Link to="/chat" className="rounded-lg bg-gold px-4 py-2 text-sm font-bold text-navy">{t('askChatbot')}</Link>
              <Link to="/programs" className="rounded-lg border border-navy/20 dark:border-white/20 px-4 py-2 text-sm font-semibold">{t('explorePrograms')}</Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
