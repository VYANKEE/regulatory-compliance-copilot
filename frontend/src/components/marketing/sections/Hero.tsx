import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { AgentPipeline } from '../AgentPipeline'
import { MagneticButton } from '../MagneticButton'

export function Hero() {
  return (
    <section className="relative flex min-h-screen items-center overflow-hidden px-6 pt-28 pb-16">
      <div className="mx-auto grid w-full max-w-6xl grid-cols-1 items-center gap-16 lg:grid-cols-[1.1fr_0.9fr]">
        <div>
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="label-tag mb-6 inline-flex items-center gap-2 rounded-full border border-[var(--border)] px-3 py-1.5"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-[var(--signal)]" />
            Agentic AI compliance system
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
            className="font-display text-5xl font-medium leading-[1.05] tracking-tight sm:text-6xl md:text-7xl"
          >
            Compliance
            <br />
            that <span className="text-gradient italic">thinks.</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.25 }}
            className="mt-7 max-w-lg text-lg leading-relaxed text-[var(--ink-soft)]"
          >
            When a new RBI circular lands, Niriksh reads it, diffs it against what came before, checks
            it against your internal policy clause by clause, and hands a human reviewer a memo with
            every claim traced back to source, not a summary you have to take on faith.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="mt-10 flex flex-wrap items-center gap-4"
          >
            <MagneticButton>
              <Link to="/signup" className="contents">
                Enter Niriksh
              </Link>
            </MagneticButton>
            <MagneticButton variant="ghost" href="#how-it-works">
              See how it works
            </MagneticButton>
          </motion.div>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.7, duration: 1 }}
            className="label-tag mt-12"
          >
            Your compliance layer, continuously thinking.
          </motion.p>
        </div>

        <motion.div
          initial={{ opacity: 0, scale: 0.94 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.9, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
          className="glass-card relative mx-auto w-full max-w-sm p-5"
        >
          <div className="label-tag mb-4 flex items-center justify-between">
            <span>Live pipeline</span>
            <span className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[var(--signal)]" />
              observing
            </span>
          </div>
          <AgentPipeline compact />
        </motion.div>
      </div>

      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-[var(--bg)] to-transparent"
      />
    </section>
  )
}
