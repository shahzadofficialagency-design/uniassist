import { useEffect, useRef } from 'react'

// Scroll-triggered 3D reveal: the wrapped block starts tilted back in
// perspective and swings upright as it enters the viewport.
export default function Reveal({ children, delay = 0, className = '' }) {
  const ref = useRef(null)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const io = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) { el.classList.add('in'); io.disconnect() }
    }, { threshold: 0.1 })
    io.observe(el)
    return () => io.disconnect()
  }, [])
  return (
    <div ref={ref} className={`reveal3d ${className}`} style={{ transitionDelay: `${delay}ms` }}>
      {children}
    </div>
  )
}

// Mouse-move 3D tilt handlers for cards (desktop pointers only in effect,
// since touch devices do not fire mousemove).
export function tiltProps(max = 7) {
  return {
    onMouseMove: (e) => {
      const el = e.currentTarget
      const r = el.getBoundingClientRect()
      const x = (e.clientX - r.left) / r.width - 0.5
      const y = (e.clientY - r.top) / r.height - 0.5
      el.style.transform = `perspective(850px) rotateY(${(x * max).toFixed(2)}deg) rotateX(${(-y * max).toFixed(2)}deg) scale(1.02)`
    },
    onMouseLeave: (e) => { e.currentTarget.style.transform = '' },
  }
}
