export default function Skeleton({ className = 'h-4 w-full' }) {
  return <div className={`animate-pulse rounded bg-slate-200 dark:bg-white/10 ${className}`} />
}

export function CardSkeleton() {
  return (
    <div className="rounded-2xl border border-slate-200 dark:border-white/10 bg-white dark:bg-white/5 p-5 space-y-3">
      <Skeleton className="h-5 w-3/4" />
      <Skeleton className="h-4 w-1/2" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-9 w-28" />
    </div>
  )
}

export function PageSkeleton({ cards = 6 }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: cards }).map((_, i) => <CardSkeleton key={i} />)}
    </div>
  )
}
