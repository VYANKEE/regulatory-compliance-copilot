/**
 * One-time cinematic title card before the landing page: loading pulse ->
 * NIRIKSH reveal -> tagline -> wipe. Once per session, skippable, respects
 * prefers-reduced-motion.
 */
import { AnimatePresence, motion } from 'framer-motion'
import { useEffect, useState } from 'react'

const SESSION_KEY = 'niriksh-intro-shown'
const WORDMARK = 'NIRIKSH'

type Phase = 'loading' | 'title' | 'tagline' | 'exiting' | 'done'

function prefersReducedMotion() {
  return typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
}

export function IntroReveal() {
  const [phase, setPhase] = useState<Phase>(() => {
    if (typeof window === 'undefined') return 'done'
    if (prefersReducedMotion() || sessionStorage.getItem(SESSION_KEY)) return 'done'
    return 'loading'
  })

  useEffect(() => {
    if (phase === 'done') return
    sessionStorage.setItem(SESSION_KEY, '1')

    const timers = [
      setTimeout(() => setPhase('title'), 650),
      setTimeout(() => setPhase('tagline'), 1750),
      setTimeout(() => setPhase('exiting'), 3100),
      setTimeout(() => setPhase('done'), 3700),
    ]
    return () => timers.forEach(clearTimeout)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function skip() {
    if (phase !== 'done') setPhase('done')
  }

  return (
    <AnimatePresence>
      {phase !== 'done' && (
        <motion.div
          key="intro"
          onClick={skip}
          initial={{ opacity: 1 }}
          animate={{ opacity: phase === 'exiting' ? 0 : 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.6, ease: 'easeInOut' }}
          className="fixed inset-0 z-[100] flex cursor-pointer flex-col items-center justify-center bg-[var(--bg)]"
        >
          {/* same film-grain overlay used on the rest of the site */}
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 opacity-[0.035] mix-blend-overlay"
            style={{
              backgroundImage:
                "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='90' height='90'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>\")",
            }}
          />
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0"
            style={{
              background: 'radial-gradient(ellipse 800px 500px at 50% 50%, rgba(84,232,178,0.10), transparent 65%)',
            }}
          />

          {phase === 'loading' && (
            <motion.span
              className="relative flex h-2.5 w-2.5 items-center justify-center"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <motion.span
                className="absolute h-full w-full rounded-full"
                style={{ background: 'var(--signal)' }}
                animate={{ opacity: [0.6, 0, 0.6], scale: [1, 2.4, 1] }}
                transition={{ duration: 1.1, repeat: Infinity, ease: 'easeOut' }}
              />
              <span className="h-2 w-2 rounded-full" style={{ background: 'var(--signal)' }} />
            </motion.span>
          )}

          {(phase === 'title' || phase === 'tagline' || phase === 'exiting') && (
            <div className="relative flex flex-col items-center">
              <h1 className="font-display flex text-5xl font-semibold tracking-tight sm:text-7xl md:text-8xl">
                {WORDMARK.split('').map((ch, i) => (
                  <motion.span
                    key={i}
                    initial={{ opacity: 0, y: 28 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.55, delay: i * 0.06, ease: [0.16, 1, 0.3, 1] }}
                  >
                    {ch}
                  </motion.span>
                ))}
              </h1>

              <AnimatePresence>
                {(phase === 'tagline' || phase === 'exiting') && (
                  <motion.p
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.6 }}
                    className="label-tag mt-6"
                  >
                    Your compliance layer, continuously thinking.
                  </motion.p>
                )}
              </AnimatePresence>
            </div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  )
}
