import { motion, useMotionValueEvent, useScroll } from 'framer-motion'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { Logo } from './Logo'

const LINKS = [
  { label: 'Product', href: '#what-is-niriksh' },
  { label: 'How It Works', href: '#how-it-works' },
  { label: 'Agents', href: '#agents' },
  { label: 'Technology', href: '#under-the-hood' },
]

export function SiteNav() {
  const [scrolled, setScrolled] = useState(false)
  const { scrollY } = useScroll()
  const { user } = useAuth()

  useMotionValueEvent(scrollY, 'change', (y) => setScrolled(y > 24))

  return (
    <motion.header
      initial={{ y: -80 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className="fixed inset-x-0 top-0 z-50 flex justify-center px-4"
    >
      <motion.div
        animate={{
          marginTop: scrolled ? 12 : 20,
          paddingInline: scrolled ? 18 : 24,
          paddingBlock: scrolled ? 8 : 12,
        }}
        transition={{ duration: 0.35, ease: 'easeOut' }}
        className={`flex w-full max-w-5xl items-center justify-between rounded-full border transition-colors duration-300 ${
          scrolled
            ? 'border-[var(--border-strong)] bg-[#0a0b0d]/90 shadow-[0_8px_32px_-12px_rgba(0,0,0,0.6)] backdrop-blur-xl'
            : 'border-transparent bg-transparent'
        }`}
      >
        <Link to="/" className="text-[var(--ink)]">
          <Logo size="sm" />
        </Link>
        <nav className="hidden items-center gap-7 md:flex">
          {LINKS.map((l) => (
            <a key={l.href} href={l.href} className="label-tag text-[var(--ink-soft)] transition-colors hover:text-[var(--ink)]">
              {l.label}
            </a>
          ))}
        </nav>
        <div className="flex items-center gap-3">
          {user ? (
            <Link to="/app" className="btn-signal rounded-full px-4 py-2 text-xs font-semibold">
              Dashboard
            </Link>
          ) : (
            <>
              <Link to="/login" className="label-tag hidden text-[var(--ink-soft)] transition-colors hover:text-[var(--ink)] sm:inline">
                Sign In
              </Link>
              <Link to="/signup" className="btn-signal rounded-full px-4 py-2 text-xs font-semibold">
                Get Started
              </Link>
            </>
          )}
        </div>
      </motion.div>
    </motion.header>
  )
}
