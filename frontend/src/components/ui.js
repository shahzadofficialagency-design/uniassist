// Shared professional button styles — one consistent look across the site.
const base =
  'inline-flex items-center justify-center gap-2 font-semibold shadow-sm transition-all duration-150 ' +
  'hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-gold focus-visible:ring-offset-2 ' +
  'active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50'

export const btnPrimary = `${base} rounded-xl bg-navy px-5 py-2.5 text-sm text-white hover:bg-navy-light`
export const btnGold = `${base} rounded-xl bg-gold px-5 py-2.5 text-sm text-navy hover:bg-gold-light`
export const btnOutline = `${base} rounded-xl border border-navy/25 bg-white/70 px-5 py-2.5 text-sm text-navy hover:border-gold dark:border-white/25 dark:bg-white/5 dark:text-white`

export const btnPrimarySm = `${base} rounded-lg bg-navy px-3.5 py-2 text-sm text-white hover:bg-navy-light`
export const btnGoldSm = `${base} rounded-lg bg-gold px-3.5 py-2 text-sm text-navy hover:bg-gold-light`
export const btnOutlineSm = `${base} rounded-lg border border-navy/25 bg-white/70 px-3.5 py-2 text-sm text-navy hover:border-gold dark:border-white/25 dark:bg-white/5 dark:text-white`
