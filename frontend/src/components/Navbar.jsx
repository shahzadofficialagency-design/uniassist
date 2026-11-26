import { useEffect, useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useLanguage } from '../context/LanguageContext'

export default function Navbar() {
  const { user, logout, isAdmin } = useAuth()
  const { lang, setLang, t } = useLanguage()
  const [open, setOpen] = useState(false)
  const [dark, setDark] = useState(() => localStorage.getItem('theme') === 'dark')
  const navigate = useNavigate()

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }, [dark])

  const links = [
    { to: '/', label: t('home') },
    { to: '/programs', label: t('programs') },
    { to: '/compare', label: t('compare') },
    { to: '/fee-calculator', label: t('feeCalculator') },
    { to: '/eligibility', label: t('eligibility') },
    { to: '/canteen', label: 'Canteen' },
    { to: '/transport', label: 'Transport' },
    { to: '/chat', label: t('chat') },
  ]
  const linkCls = ({ isActive }) =>
    `px-3 py-2 rounded-lg text-sm font-medium ${isActive ? 'bg-white/15 text-white' : 'text-white/80 hover:text-white hover:bg-white/10'}`

  return (
    <header className="sticky top-0 z-40 bg-navy shadow-md">
      <div className="mx-auto flex max-w-7xl items-center gap-2 px-3 py-2.5 sm:gap-3 sm:px-4">
        <Link to="/" className="flex items-center gap-2 sm:gap-3 shrink-0">
          <span className="grid h-11 w-11 place-items-center overflow-hidden rounded-full bg-white">
            <img src="/assets/iub-logo.jpg" alt="IUB Logo" className="h-10 w-10 object-contain" />
          </span>
          <span className="leading-tight">
            <span className="block font-extrabold text-white tracking-tight">UniAssist</span>
            <span className="hidden min-[420px]:block text-[11px] text-gold-light">Islamia University of Bahawalpur</span>
          </span>
        </Link>

        <nav className="ms-auto hidden lg:flex items-center gap-1">
          {links.map((l) => <NavLink key={l.to} to={l.to} className={linkCls}>{l.label}</NavLink>)}
          {user && <NavLink to="/dashboard" className={linkCls}>{t('dashboard')}</NavLink>}
          {isAdmin && <NavLink to="/admin" className={linkCls}>{t('admin')}</NavLink>}
        </nav>

        <div className="ms-auto lg:ms-0 flex items-center gap-2">
          <button
            onClick={() => setLang(lang === 'en' ? 'ur' : 'en')}
            className="rounded-full border border-white/25 px-3 py-1.5 text-xs font-bold text-white hover:bg-white/10"
            aria-label="Switch language"
          >
            {lang === 'en' ? 'اردو' : 'EN'}
          </button>
          <button
            onClick={() => setDark(!dark)}
            className="rounded-full border border-white/25 px-3 py-1.5 text-xs text-white hover:bg-white/10"
            aria-label="Toggle dark mode"
          >
            {dark ? '☀️' : '🌙'}
          </button>
          {user ? (
            <>
              <Link to="/profile" className="hidden sm:block rounded-full bg-gold px-3.5 py-1.5 text-xs font-bold text-navy">{user.name?.split(' ')[0] || t('profile')}</Link>
              <button onClick={() => { logout(); navigate('/') }} className="hidden sm:block text-xs font-semibold text-white/80 hover:text-white">{t('logout')}</button>
            </>
          ) : (
            <>
              <Link to="/login" className="hidden sm:inline-block rounded-full px-3 py-1.5 text-xs font-bold text-white hover:bg-white/10">{t('login')}</Link>
              <Link to="/register" className="hidden sm:inline-block rounded-full bg-gold px-3.5 py-1.5 text-xs font-bold text-navy">{t('register')}</Link>
            </>
          )}
          <button onClick={() => setOpen(!open)} className="lg:hidden rounded-lg p-2 text-white" aria-label="Menu">☰</button>
        </div>
      </div>

      {open && (
        <nav className="lg:hidden border-t border-white/10 px-4 py-3 flex flex-col gap-1">
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} onClick={() => setOpen(false)} className="rounded-lg px-3 py-2 text-sm text-white/90 hover:bg-white/10">{l.label}</NavLink>
          ))}
          {user && <NavLink to="/dashboard" onClick={() => setOpen(false)} className="rounded-lg px-3 py-2 text-sm text-white/90 hover:bg-white/10">{t('dashboard')}</NavLink>}
          {isAdmin && <NavLink to="/admin" onClick={() => setOpen(false)} className="rounded-lg px-3 py-2 text-sm text-white/90 hover:bg-white/10">{t('admin')}</NavLink>}
          {!user && <NavLink to="/login" onClick={() => setOpen(false)} className="rounded-lg px-3 py-2 text-sm font-bold text-white hover:bg-white/10">{t('login')}</NavLink>}
          {!user && <NavLink to="/register" onClick={() => setOpen(false)} className="rounded-lg px-3 py-2 text-sm font-bold text-gold hover:bg-white/10">{t('register')}</NavLink>}
          {user && <NavLink to="/profile" onClick={() => setOpen(false)} className="rounded-lg px-3 py-2 text-sm text-white/90 hover:bg-white/10">{t('profile')}</NavLink>}
          {user && <button onClick={() => { logout(); setOpen(false); navigate('/') }} className="text-start rounded-lg px-3 py-2 text-sm text-white/90 hover:bg-white/10">{t('logout')}</button>}
        </nav>
      )}
    </header>
  )
}
