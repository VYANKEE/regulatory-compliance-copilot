/** Real thread workflow status (pending -> awaiting_approval -> completed/rejected/failed). */
const META: Record<string, { label: string; color: string; pulse?: boolean }> = {
  pending: { label: 'Running', color: 'var(--cyan)', pulse: true },
  awaiting_approval: { label: 'Needs review', color: 'var(--amber)', pulse: true },
  completed: { label: 'Approved', color: 'var(--signal)' },
  rejected: { label: 'Rejected', color: 'var(--red)' },
  failed: { label: 'Failed', color: 'var(--red)' },
}

export function StatusBadge({ status }: { status: string }) {
  const meta = META[status] ?? { label: status, color: 'var(--ink-faint)' }
  return (
    <span
      className="inline-flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium"
      style={{ color: meta.color, background: `${meta.color}1a`, border: `1px solid ${meta.color}40` }}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${meta.pulse ? 'animate-pulse' : ''}`} style={{ background: meta.color }} />
      {meta.label}
    </span>
  )
}

/** Real finding status -- Met / Partial / Not Met, exactly as the Impact/Verifier agents produce. */
const FINDING_META: Record<string, string> = {
  Met: 'var(--signal)',
  Partial: 'var(--amber)',
  'Not Met': 'var(--red)',
}

export function FindingBadge({ status }: { status: string }) {
  const color = FINDING_META[status] ?? 'var(--ink-faint)'
  return (
    <span
      className="inline-flex shrink-0 items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
      style={{ color, background: `${color}1a`, border: `1px solid ${color}40` }}
    >
      {status}
    </span>
  )
}
