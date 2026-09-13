/**
 * The flagship "agents thinking" visualization. Renders the real pipeline
 * (see lib/agents.ts) as connected nodes with a traveling signal that loops
 * through them -- used on the landing hero (compact, vertical) and again,
 * larger, in the "How It Works" section. `activeId`/`states` let the same
 * component later show REAL live status during an actual run (Phase 3 of
 * this rebuild) instead of the idle demo loop -- when `states` is passed,
 * the animation stops guessing and reflects the real thread status.
 */
import { AnimatePresence, motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import { AGENTS, HUMAN_REVIEW } from '../../lib/agents'

export type AgentRunState = 'idle' | 'queued' | 'running' | 'complete' | 'error'

const STATE_COLOR: Record<AgentRunState, string> = {
  idle: 'var(--ink-faint)',
  queued: 'var(--ink-soft)',
  running: 'var(--signal)',
  complete: 'var(--signal)',
  error: 'var(--red)',
}

export function AgentPipeline({
  orientation = 'vertical',
  states,
  onSelect,
  compact = false,
}: {
  orientation?: 'vertical' | 'horizontal'
  /** Real per-agent state, keyed by agent id. Omit for the idle decorative loop. */
  states?: Record<string, AgentRunState>
  onSelect?: (id: string) => void
  compact?: boolean
}) {
  const nodes = [...AGENTS, HUMAN_REVIEW]
  const [demoActive, setDemoActive] = useState(0)

  // idle decorative loop, only when no real states are supplied
  useEffect(() => {
    if (states) return
    const t = setInterval(() => setDemoActive((i) => (i + 1) % nodes.length), 1400)
    return () => clearInterval(t)
  }, [states, nodes.length])

  const isVertical = orientation === 'vertical'

  return (
    <div className={`flex ${isVertical ? 'flex-col' : 'flex-row flex-wrap items-start justify-center'} gap-0`}>
      {nodes.map((n, i) => {
        const state: AgentRunState = states ? states[n.id] ?? 'idle' : i === demoActive ? 'running' : i < demoActive ? 'complete' : 'idle'
        const color = STATE_COLOR[state]
        return (
          <div key={n.id} className={`flex ${isVertical ? 'flex-row items-stretch' : 'flex-col items-center'}`}>
            <button
              type="button"
              onClick={() => onSelect?.(n.id)}
              className={`group relative flex items-center gap-3 rounded-xl border px-4 py-3 text-left transition-colors ${
                compact ? 'min-w-[11rem]' : 'min-w-[13rem]'
              }`}
              style={{
                borderColor: state === 'running' ? 'var(--border-signal)' : 'var(--border)',
                background: state === 'running' ? 'rgba(84,232,178,0.06)' : 'var(--surface)',
              }}
            >
              <span className="relative flex h-2.5 w-2.5 shrink-0 items-center justify-center">
                <AnimatePresence>
                  {state === 'running' && (
                    <motion.span
                      className="absolute h-full w-full rounded-full"
                      style={{ background: color }}
                      initial={{ opacity: 0.6, scale: 1 }}
                      animate={{ opacity: 0, scale: 2.6 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 1.1, repeat: Infinity, ease: 'easeOut' }}
                    />
                  )}
                </AnimatePresence>
                <span className="h-2 w-2 rounded-full" style={{ background: color }} />
              </span>
              <span className="min-w-0">
                <span className={`block font-medium leading-tight ${compact ? 'text-xs' : 'text-sm'}`}>{n.name}</span>
                <span className="label-tag block truncate" style={{ color }}>
                  {state === 'idle' && 'WAITING'}
                  {state === 'queued' && 'QUEUED'}
                  {state === 'running' && 'RUNNING'}
                  {state === 'complete' && 'COMPLETE'}
                  {state === 'error' && 'ERROR'}
                </span>
              </span>
            </button>
            {i < nodes.length - 1 && (
              <div className={isVertical ? 'ml-[1.15rem] h-6 w-px' : 'mx-1 mt-6 h-px w-6'} style={{ background: 'var(--border)' }} />
            )}
          </div>
        )
      })}
    </div>
  )
}
