/**
 * Fills the side space next to the live agent list with what that agent
 * actually does — reusing the exact copy from lib/agents.ts (the same
 * single source of truth used on the landing "Agents" section), not new
 * invented text. Mirrors the active/detail-pane pattern already used in
 * marketing/sections/HowItWorks.tsx (AnimatePresence mode="wait", keyed by
 * id) so the live-run screen and the marketing page feel like one system.
 */
import { AnimatePresence, motion } from 'framer-motion'
import type { AgentSpec } from '../../lib/agents'
import type { AgentRunState } from './AgentPipeline'

type Agent = AgentSpec | { id: string; name: string; role: string }

const STATE_LABEL: Record<AgentRunState, string> = {
  idle: 'Waiting',
  queued: 'Queued next',
  running: 'Running now',
  complete: 'Complete',
  error: 'Error',
}

const STATE_COLOR: Record<AgentRunState, string> = {
  idle: 'var(--ink-faint)',
  queued: 'var(--ink-soft)',
  running: 'var(--signal)',
  complete: 'var(--signal)',
  error: 'var(--red)',
}

export function AgentDetailPanel({ agent, state }: { agent: Agent; state?: AgentRunState }) {
  const full = agent as AgentSpec

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={agent.id}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        transition={{ duration: 0.3 }}
        className="glass-card flex h-full flex-col p-6"
        style={{ borderColor: state === 'running' ? 'var(--border-signal)' : undefined }}
      >
        <div className="mb-3 flex items-center justify-between gap-3">
          <p className="font-display text-lg font-medium leading-tight">{agent.name}</p>
          {state && (
            <span className="label-tag shrink-0" style={{ color: STATE_COLOR[state] }}>
              {STATE_LABEL[state]}
            </span>
          )}
        </div>
        <p className="text-sm leading-relaxed text-[var(--ink-soft)]">{agent.role}</p>

        {full.receives && (
          <div className="mt-5 grid flex-1 content-start gap-4 border-t border-[var(--border)] pt-4 sm:grid-cols-2">
            <Field label="Receives" value={full.receives} />
            <Field label="Analyzes" value={full.analyzes} />
            <Field label="Tools" value={full.tools} />
            <Field label="Produces" value={full.produces} />
          </div>
        )}
      </motion.div>
    </AnimatePresence>
  )
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="label-tag mb-1 text-[var(--ink-faint)]">{label}</p>
      <p className="text-xs leading-relaxed text-[var(--ink-soft)]">{value}</p>
    </div>
  )
}
