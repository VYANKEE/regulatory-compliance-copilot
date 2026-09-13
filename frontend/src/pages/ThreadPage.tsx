import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import { approveAnalysis, getThread, type ThreadOut } from '../lib/api'
import { AgentPipeline, type AgentRunState } from '../components/marketing/AgentPipeline'
import { AgentDetailPanel } from '../components/marketing/AgentDetailPanel'
import { AGENTS, HUMAN_REVIEW } from '../lib/agents'
import { StatusBadge, FindingBadge } from '../components/app/StatusBadge'
import { ErrorState, LoadingScreen } from '../components/app/States'
import { FollowUpChat } from '../components/app/FollowUpChat'
import { MagneticButton } from '../components/marketing/MagneticButton'
import { Reveal, RevealGroup, RevealItem } from '../components/marketing/Reveal'

// Analysis runs in a background worker -- poll while status is "pending".
const POLL_INTERVAL_MS = 4000

export function ThreadPage() {
  const { threadId } = useParams<{ threadId: string }>()
  const [thread, setThread] = useState<ThreadOut | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [feedback, setFeedback] = useState('')
  const [deciding, setDeciding] = useState(false)
  const [decisionOutcome, setDecisionOutcome] = useState<'approved' | 'rejected' | null>(null)
  const [now, setNow] = useState(Date.now())

  async function load() {
    if (!threadId) return
    try {
      const t = await getThread(threadId)
      setThread(t)
      setError(null)
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Could not load this analysis.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [threadId])

  useEffect(() => {
    if (thread?.status !== 'pending') return
    const interval = setInterval(load, POLL_INTERVAL_MS)
    return () => clearInterval(interval)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [thread?.status, threadId])

  // real wall-clock ticker, only runs while the analysis is actually in flight
  useEffect(() => {
    if (thread?.status !== 'pending') return
    const t = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(t)
  }, [thread?.status])

  async function decide(approved: boolean) {
    if (!threadId) return
    if (!approved && !feedback.trim()) {
      setError('Please add a short note explaining why you\'re rejecting this. It\'s recorded in the audit log.')
      return
    }
    setDeciding(true)
    setError(null)
    try {
      const updated = await approveAnalysis(threadId, approved, feedback)
      setThread(updated)
      setDecisionOutcome(approved ? 'approved' : 'rejected')
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Could not record your decision. Nothing was changed. You can try again.')
    } finally {
      setDeciding(false)
    }
  }

  const elapsedSec = thread ? Math.max(0, Math.floor((now - new Date(thread.created_at).getTime()) / 1000)) : 0

  // No live per-agent status endpoint yet -- this estimates stage from elapsed time.
  const runStates: Record<string, AgentRunState> = useMemo(() => {
    const thresholds = [5, 30, 90, 180, 230, 250] // seconds, rough real-run shape
    const ids = [...AGENTS.map((a) => a.id), 'human']
    const states: Record<string, AgentRunState> = {}
    ids.forEach((id, i) => {
      if (id === 'human') {
        states[id] = 'idle'
        return
      }
      const t = thresholds[i] ?? thresholds[thresholds.length - 1]
      states[id] = elapsedSec < t ? (i === 0 || elapsedSec > (thresholds[i - 1] ?? 0) ? 'running' : 'queued') : 'complete'
    })
    return states
  }, [elapsedSec])

  // Node whose description fills the side panel: running, else last completed, else first.
  const allNodes = useMemo(() => [...AGENTS, HUMAN_REVIEW], [])
  const { activeAgent, activeState } = useMemo(() => {
    const running = allNodes.find((n) => runStates[n.id] === 'running')
    if (running) return { activeAgent: running, activeState: runStates[running.id] }
    const completed = allNodes.filter((n) => runStates[n.id] === 'complete')
    if (completed.length > 0) {
      const last = completed[completed.length - 1]
      return { activeAgent: last, activeState: runStates[last.id] }
    }
    return { activeAgent: allNodes[0], activeState: runStates[allNodes[0].id] }
  }, [runStates, allNodes])

  if (loading) return <LoadingScreen label="Loading analysis…" />
  if (error && !thread) return <ErrorState detail={error} onRetry={load} />
  if (!thread) return null

  const notMet = thread.findings.filter((f) => f.status === 'Not Met')
  const partial = thread.findings.filter((f) => f.status === 'Partial')
  const met = thread.findings.filter((f) => f.status === 'Met')

  return (
    <div>
      <Reveal>
        <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="label-tag mb-1 text-[var(--ink-faint)]">Analysis</p>
            <h1 className="font-display text-3xl font-medium">{thread.circular_ref}</h1>
          </div>
          <StatusBadge status={thread.status} />
        </div>
      </Reveal>

      {/* live execution experience */}
      {thread.status === 'pending' && (
        <Reveal className="glass-card mb-8 p-8">
          <div className="mb-6 flex items-center justify-between">
            <p className="font-display text-xl font-medium">Niriksh is thinking</p>
            <span className="font-mono-ui text-sm text-[var(--ink-soft)]">
              {String(Math.floor(elapsedSec / 60)).padStart(2, '0')}:{String(elapsedSec % 60).padStart(2, '0')}
            </span>
          </div>
          <div className="grid gap-5 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)]">
            <AgentPipeline states={runStates} compact />
            <AgentDetailPanel agent={activeAgent} state={activeState} />
          </div>
        </Reveal>
      )}

      {thread.status === 'failed' && (
        <ErrorState
          title="This analysis run failed."
          detail="The backend retries transient provider failures automatically before giving up. If you're seeing this, every retry was exhausted. Start a new analysis to try again."
        />
      )}

      {/* Any error from a failed decision or poll -- always visible. */}
      {error && thread && (
        <div className="glass-card mb-6 border-[var(--red)]/30 p-4">
          <p className="text-sm text-[var(--red)]">{error}</p>
        </div>
      )}

      {decisionOutcome && thread.status !== 'awaiting_approval' && (
        <div className="glass-card mb-6 p-4" style={{ borderColor: 'var(--border-signal)' }}>
          <p className="text-sm">
            {decisionOutcome === 'approved'
              ? '✓ Approved. This memo is now finalized and recorded in the audit log.'
              : '✕ Rejected. This analysis was withheld, not deleted; your feedback was recorded in the audit log.'}
          </p>
        </div>
      )}

      {thread.status === 'awaiting_approval' && (
        <Reveal className="glass-card mb-8 border-[var(--amber)]/30 p-6">
          <p className="font-display mb-1 text-lg font-medium">Your decision is needed</p>
          <p className="mb-4 text-sm leading-relaxed text-[var(--ink-soft)]">
            This memo was generated by the AI pipeline and independently re-checked by the Verifier
            Agent, but nothing here is final until you decide. <strong>Approve</strong> to finalize it
            as-is, or <strong>Reject</strong> and add a note explaining why (this becomes part of the
            audit record, not a message sent anywhere).
          </p>
          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Feedback (optional if approving, required if rejecting)"
            className="field mb-4 w-full rounded-lg px-3.5 py-2.5 text-sm"
            rows={2}
          />
          <div className="flex gap-2">
            <MagneticButton onClick={() => decide(true)} disabled={deciding}>
              {deciding ? 'Recording…' : 'Approve & Deliver'}
            </MagneticButton>
            <button
              onClick={() => decide(false)}
              disabled={deciding}
              className="rounded-full border border-[var(--red)]/40 px-6 py-3 text-sm font-medium text-[var(--red)] transition hover:bg-[var(--red)]/10 disabled:opacity-50"
            >
              {deciding ? 'Recording…' : 'Reject'}
            </button>
          </div>
        </Reveal>
      )}

      {thread.findings.length > 0 && (
        <div className="mb-8">
          <div className="mb-4 flex items-center justify-between">
            <p className="label-tag text-[var(--ink-faint)]">Verified findings ({thread.findings.length})</p>
            <p className="label-tag text-[var(--ink-faint)]">
              {notMet.length} not met · {partial.length} partial · {met.length} met
            </p>
          </div>
          <RevealGroup className="grid gap-2.5" stagger={0.03}>
            {thread.findings.map((f) => (
              <RevealItem key={f.id}>
                <div className="glass-card p-5">
                  <div className="mb-2 flex items-center justify-between gap-3">
                    <p className="text-sm font-medium">{f.requirement}</p>
                    <FindingBadge status={f.status} />
                  </div>
                  <p className="mb-2 text-sm leading-relaxed text-[var(--ink-soft)]">{f.explanation}</p>
                  {f.suggested_policy_change && (
                    <p className="mb-3 text-sm leading-relaxed text-[var(--ink-soft)]">
                      <span className="font-medium text-[var(--ink)]">Suggested change:</span> {f.suggested_policy_change}
                    </p>
                  )}
                  <span
                    title="Clause lookup endpoint not built yet"
                    className="font-mono-ui inline-block rounded bg-white/5 px-2 py-0.5 text-xs text-[var(--ink-soft)]"
                  >
                    {f.rbi_citation}
                  </span>
                </div>
              </RevealItem>
            ))}
          </RevealGroup>
        </div>
      )}

      {thread.findings.length > 0 && (
        <Reveal className="glass-card mb-8 p-6">
          <p className="label-tag mb-3 text-[var(--ink-faint)]">Agent trail</p>
          <div className="flex flex-wrap gap-2">
            {AGENTS.map((a) => (
              <span key={a.id} className="label-tag rounded-full border border-[var(--border)] px-3 py-1.5 text-[var(--ink-soft)]">
                {a.name}
              </span>
            ))}
          </div>
        </Reveal>
      )}

      <Reveal className="glass-card mb-8 p-6">
        <p className="label-tag mb-3 text-[var(--ink-faint)]">Report</p>
        <div className="prose prose-sm prose-invert max-w-none prose-headings:font-display">
          <ReactMarkdown>{thread.report || '_No report yet._'}</ReactMarkdown>
        </div>
      </Reveal>

      {/* Real follow-up Q&A, grounded in retrieved RBI clauses per question. */}
      {threadId && <FollowUpChat threadId={threadId} findings={thread.findings} />}
    </div>
  )
}
