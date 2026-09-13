import { useEffect, useMemo, useState, type MouseEvent } from 'react'
import { Link } from 'react-router-dom'
import { Trash2 } from 'lucide-react'
import { deleteThread, listThreads, type ThreadSummary } from '../lib/api'
import { StatusBadge } from '../components/app/StatusBadge'
import { StatCard } from '../components/app/StatCard'
import { EmptyState, ErrorState, LoadingScreen } from '../components/app/States'
import { MagneticButton } from '../components/marketing/MagneticButton'
import { Reveal, RevealGroup, RevealItem } from '../components/marketing/Reveal'

/**
 * Every number on this page is computed directly from the real
 * GET /analysis/ response -- nothing here is a placeholder metric. There is
 * no "AI confidence" or "risk level" card because the backend doesn't
 * produce either; "Avg. turnaround" is genuinely derived from
 * updated_at - created_at on threads that have actually finished.
 */
export function DashboardPage() {
  const [threads, setThreads] = useState<ThreadSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  function load() {
    setLoading(true)
    setError(null)
    listThreads()
      .then(setThreads)
      .catch((e) => setError(e?.response?.data?.detail ?? 'Failed to load analyses.'))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  async function handleDelete(e: MouseEvent, threadId: string) {
    e.preventDefault()
    e.stopPropagation()
    if (!confirm('Delete this analysis? This cannot be undone.')) return
    setDeletingId(threadId)
    const prev = threads
    setThreads((ts) => ts.filter((t) => t.id !== threadId))
    try {
      await deleteThread(threadId)
    } catch (err: any) {
      setThreads(prev)
      setError(err?.response?.data?.detail ?? 'Could not delete this analysis.')
    } finally {
      setDeletingId(null)
    }
  }

  const stats = useMemo(() => {
    const total = threads.length
    const pendingReview = threads.filter((t) => t.status === 'awaiting_approval').length
    const running = threads.filter((t) => t.status === 'pending').length
    const completed = threads.filter((t) => t.status === 'completed').length

    const finished = threads.filter((t) => t.status === 'completed' || t.status === 'rejected')
    let avgTurnaround = 'N/A'
    if (finished.length > 0) {
      const totalMs = finished.reduce((sum, t) => sum + (new Date(t.updated_at).getTime() - new Date(t.created_at).getTime()), 0)
      const avgMs = totalMs / finished.length
      avgTurnaround = avgMs < 60_000 ? `${Math.round(avgMs / 1000)}s` : `${(avgMs / 60_000).toFixed(1)}m`
    }

    return { total, pendingReview, running, completed, avgTurnaround }
  }, [threads])

  if (loading) return <LoadingScreen label="Loading your analyses…" />

  return (
    <div>
      <Reveal>
        <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="label-tag mb-1 text-[var(--ink-faint)]">Command center</p>
            <h1 className="font-display text-3xl font-medium">Your Analyses</h1>
          </div>
          <MagneticButton>
            <Link to="/app/new" className="contents">
              + New Analysis
            </Link>
          </MagneticButton>
        </div>
      </Reveal>

      {error && <ErrorState detail={error} onRetry={load} />}

      {!error && (
        <RevealGroup className="mb-8 grid grid-cols-2 gap-3 sm:grid-cols-4" stagger={0.05}>
          <RevealItem>
            <StatCard label="Total cases" value={String(stats.total)} />
          </RevealItem>
          <RevealItem>
            <StatCard label="Needs review" value={String(stats.pendingReview)} hint="Awaiting human approval" />
          </RevealItem>
          <RevealItem>
            <StatCard label="Running" value={String(stats.running)} hint="Pipeline in progress" />
          </RevealItem>
          <RevealItem>
            <StatCard label="Avg. turnaround" value={stats.avgTurnaround} hint={`Across ${stats.completed + threads.filter((t) => t.status === 'rejected').length} finished`} />
          </RevealItem>
        </RevealGroup>
      )}

      {!error && threads.length === 0 && (
        <EmptyState
          title="Your compliance intelligence starts here."
          detail="Upload a policy document and pick a circular to run your first analysis."
          actionLabel="Run your first analysis"
          actionTo="/app/new"
        />
      )}

      {!error && threads.length > 0 && (
        <RevealGroup className="grid gap-3" stagger={0.04}>
          {threads.map((t) => (
            <RevealItem key={t.id}>
              <Link
                to={`/app/threads/${t.id}`}
                className="glass-card glass-card-hover group flex items-center justify-between px-5 py-4"
              >
                <div className="min-w-0">
                  <p className="truncate font-medium">{t.circular_ref}</p>
                  <p className="label-tag mt-0.5 text-[var(--ink-faint)]">{new Date(t.created_at).toLocaleString()}</p>
                </div>
                <div className="flex shrink-0 items-center gap-4">
                  <StatusBadge status={t.status} />
                  <button
                    type="button"
                    onClick={(e) => handleDelete(e, t.id)}
                    disabled={deletingId === t.id}
                    title="Delete this analysis"
                    className="rounded-md p-1.5 text-[var(--ink-faint)] opacity-0 transition hover:bg-[var(--red)]/10 hover:text-[var(--red)] group-hover:opacity-100 disabled:opacity-50"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </Link>
            </RevealItem>
          ))}
        </RevealGroup>
      )}
    </div>
  )
}
