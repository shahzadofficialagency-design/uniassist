import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'

export default function Canteen() {
  const [data, setData] = useState({ title: '', source: '', note: '', items: [] })
  const [q, setQ] = useState('')
  const [cat, setCat] = useState('')

  useEffect(() => {
    api.get('/canteen').then(({ data }) => setData(data)).catch(() => {})
  }, [])

  const categories = useMemo(() => [...new Set(data.items.map((i) => i.category))], [data])
  const shown = data.items.filter((i) =>
    (!cat || i.category === cat) &&
    (!q || i.name.toLowerCase().includes(q.toLowerCase())))

  const price = (r) => (r.startsWith('As per') ? r : `Rs ${r}`)

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <h1 className="text-3xl font-extrabold text-navy dark:text-white">Campus Canteens 🍽️</h1>
      <p className="mt-1 text-sm text-slate-500">
        Heritage Cafe, Main Canteen and all other canteens/messes/tuck shops at IUB Bahawalpur campuses follow one official rate list.
      </p>

      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        <img src="/images/heritage-cafe.jpg" alt="Heritage Cafe" className="h-52 w-full rounded-2xl border border-slate-200 dark:border-white/10 object-cover" />
        <img src="/images/main-canteen.jpg" alt="Main Canteen IUB" className="h-52 w-full rounded-2xl border border-slate-200 dark:border-white/10 object-cover" />
      </div>

      <div className="mt-6 rounded-2xl border border-slate-200 dark:border-white/10 bg-white dark:bg-white/5 p-5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-lg font-extrabold text-navy dark:text-white">{data.title || 'Rate List 2026-27'}</h2>
          <span className="rounded-full bg-gold/10 px-3 py-1 text-xs font-bold text-navy dark:text-gold">{data.items.length} items</span>
        </div>

        <div className="mt-4 flex flex-col gap-2 sm:flex-row">
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search an item — e.g. burger, biryani, chai…"
            className="flex-1 rounded-full border border-slate-300 dark:border-white/20 bg-transparent px-4 py-2.5 text-sm outline-none focus:border-gold" />
          <div className="flex flex-wrap gap-1.5">
            <button onClick={() => setCat('')} className={`rounded-full px-3 py-2 text-xs font-bold ${cat === '' ? 'bg-navy text-white' : 'border border-slate-300 dark:border-white/20'}`}>All</button>
            {categories.map((c) => (
              <button key={c} onClick={() => setCat(c)} className={`rounded-full px-3 py-2 text-xs font-bold ${cat === c ? 'bg-navy text-white' : 'border border-slate-300 dark:border-white/20'}`}>{c}</button>
            ))}
          </div>
        </div>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[520px] text-sm">
            <thead>
              <tr className="border-b border-slate-200 dark:border-white/10 text-left text-slate-500">
                <th className="py-2 pe-3 font-semibold">Item</th>
                <th className="py-2 pe-3 font-semibold">Weight / Size</th>
                <th className="py-2 pe-3 font-semibold">Category</th>
                <th className="py-2 font-semibold text-end">Rate</th>
              </tr>
            </thead>
            <tbody>
              {shown.map((i, idx) => (
                <tr key={idx} className="border-b border-slate-100 dark:border-white/5 hover:bg-gold/5">
                  <td className="py-2 pe-3 font-semibold">{i.name}</td>
                  <td className="py-2 pe-3 text-slate-500">{i.weight || '—'}</td>
                  <td className="py-2 pe-3 text-slate-500">{i.category}</td>
                  <td className="py-2 text-end font-extrabold text-navy dark:text-gold">{price(i.rate)}</td>
                </tr>
              ))}
              {shown.length === 0 && (
                <tr><td colSpan="4" className="py-6 text-center text-slate-400">No item matches your search.</td></tr>
              )}
            </tbody>
          </table>
        </div>

        {data.note && <p className="mt-3 text-xs text-slate-500">Note: {data.note}</p>}
        <p className="mt-1 text-xs text-slate-400">Source: {data.source}</p>
        <p className="mt-3 text-sm">
          Kisi item ki price chatbot se bhi pooch sakte hain:{' '}
          <Link to="/chat" state={{ prefill: 'Canteen mein chicken burger kitne ka hai?' }} className="font-bold text-gold hover:underline">
            “Canteen mein chicken burger kitne ka hai?” →
          </Link>
        </p>
      </div>
    </div>
  )
}
