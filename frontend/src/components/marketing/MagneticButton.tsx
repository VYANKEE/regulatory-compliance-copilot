/** Button that leans toward the cursor on hover -- kept subtle, not a gimmick. */
import { motion } from 'framer-motion'
import { type ReactNode, useRef, useState } from 'react'

export function MagneticButton({
  children,
  onClick,
  href,
  variant = 'signal',
  className = '',
  type = 'button',
  disabled = false,
}: {
  children: ReactNode
  onClick?: () => void
  href?: string
  variant?: 'signal' | 'ghost'
  className?: string
  type?: 'button' | 'submit'
  disabled?: boolean
}) {
  const ref = useRef<HTMLButtonElement | HTMLAnchorElement>(null)
  const [pos, setPos] = useState({ x: 0, y: 0 })

  function handleMove(e: React.MouseEvent) {
    const el = ref.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    const x = e.clientX - rect.left - rect.width / 2
    const y = e.clientY - rect.top - rect.height / 2
    setPos({ x: x * 0.25, y: y * 0.35 })
  }
  function handleLeave() {
    setPos({ x: 0, y: 0 })
  }

  const base =
    variant === 'signal'
      ? 'btn-signal rounded-full px-7 py-3.5 text-sm'
      : 'btn-ghost rounded-full px-7 py-3.5 text-sm'

  const content = (
    <motion.span
      className="inline-flex items-center gap-2"
      animate={{ x: pos.x, y: pos.y }}
      transition={{ type: 'spring', stiffness: 200, damping: 12, mass: 0.4 }}
    >
      {children}
    </motion.span>
  )

  if (href) {
    return (
      <a
        ref={ref as React.RefObject<HTMLAnchorElement>}
        href={href}
        onMouseMove={handleMove}
        onMouseLeave={handleLeave}
        className={`inline-flex items-center justify-center font-medium ${base} ${className}`}
      >
        {content}
      </a>
    )
  }

  return (
    <button
      ref={ref as React.RefObject<HTMLButtonElement>}
      type={type}
      disabled={disabled}
      onClick={onClick}
      onMouseMove={handleMove}
      onMouseLeave={handleLeave}
      className={`inline-flex items-center justify-center font-medium ${base} ${className}`}
    >
      {content}
    </button>
  )
}
