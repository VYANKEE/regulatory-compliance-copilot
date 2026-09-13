import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Search } from 'lucide-react'
import { listThreads, type ThreadSummary } from '../lib/api'
import { StatusBadge } from '../components/app/StatusBadge'
import { EmptyState, ErrorState, LoadingScreen } from '../components/app/States'
import { Reveal, RevealGroup, RevealItem } from '../components/marketing/Reveal'

const STATUS_FILTERS = ['all', 'pending', 'awaiting_approval', 'completed', 'rejected', 'failed'] as const

export function HistoryPage() {
  const [threads, setThreads] = useState<ThreadSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState<(typeof STATUS_FILTERS)[number]>('all')

  function load() {
    setLoading(true)
    listThreads()
      .then(setThreads)
      .catch((e) => setError(e?.response?.data?.detail ?? 'Failed to load history.'))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const filtered = useMemo(() => {
    return threads
      .filter((t) => status === 'all' || t.status === status)
      .filter((t) => t.circular_ref.toLowerCase().includes(query.toLowerCase()))
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
  }, [threads, query, status])

  if (loading) return <LoadingScreen label="Loading history…" />

  return (
    <div>
      <Reveal>
        <p className="label-tag mb-1 text-[var(--ink-faint)]">Every past run</p>
        <h1 className="font-display text-3xl font-medium">History</h1>
      </Reveal>

      {error && <ErrorState detail={error} onRetry={load} />}

      {!error && (
        <Reveal delay={0.05} className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="field flex flex-1 items-center gap-2 rounded-full px-4 py-2.5">
            <Search size={15} className="text-[var(--ink-faint)]" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by circular reference…"
              className="w-full bg-transparent text-sm outline-none"
            />
          </div>
          <div className="flex flex-wrap gap-2">
            {STATUS_FILTERS.map((s) => (
              <button
                key={s}
                onClick={() => setStatus(s)}
                className="label-tag rounded-full border px-3 py-1.5 transition-colors"
                style={{
                  borderColor: status === s ? 'var(--border-signal)' : 'var(--border)',
                  color: status === s ? 'var(--signal)' : 'var(--ink-soft)',
                  background: status === s ? 'rgba(84,232,178,0.06)' : 'transparent',
                }}
              >
                {s === 'all' ? 'All' : s.replace('_', ' ')}
              </button>
            ))}
          </div>
        </Reveal>
      )}

      {!error && filtered.length === 0 && (
        <div className="mt-6">
          <EmptyState title="No matching analyses." detail="Try a different search term or status filter." />
        </div>
      )}

      {!error && filtered.length > 0 && (
        <RevealGroup className="mt-6 grid gap-2.5" stagger={0.03}>
          {filtered.map((t) => (
            <RevealItem key={t.id}>
              <Link to={`/app/threads/${t.id}`} className="glass-card glass-card-hover flex items-center justify-between px-5 py-4">
                <div className="min-w-0">
                  <p className="truncate font-medium">{t.circular_ref}</p>
                  <p className="label-tag mt-0.5 text-[var(--ink-faint)]">
                    Created {new Date(t.created_at).toLocaleString()} · Updated {new Date(t.updated_at).toLocaleString()}
                  </p>
                </div>
                <StatusBadge status={t.status} />
              </Link>
            </RevealItem>
          ))}
        </RevealGroup>
      )}
    </div>
  )
}
