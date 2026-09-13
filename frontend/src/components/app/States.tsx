/** Shared empty / error / loading states -- designed, not plain "No data" text. */
import { Link } from 'react-router-dom'
import { AgentPipeline } from '../marketing/AgentPipeline'
import { MagneticButton } from '../marketing/MagneticButton'

export function EmptyState({
  title,
  detail,
  actionLabel,
  actionTo,
}: {
  title: string
  detail: string
  actionLabel?: string
  actionTo?: string
}) {
  return (
    <div className="glass-card px-8 py-16 text-center">
      <p className="label-tag mb-3 text-[var(--ink-faint)]">Nothing here yet</p>
      <h3 className="font-display text-xl font-medium">{title}</h3>
      <p className="mx-auto mt-2 max-w-sm text-sm leading-relaxed text-[var(--ink-soft)]">{detail}</p>
      {actionLabel && actionTo && (
        <div className="mt-7 flex justify-center">
          <MagneticButton>
            <Link to={actionTo} className="contents">
              {actionLabel}
            </Link>
          </MagneticButton>
        </div>
      )}
    </div>
  )
}

export function ErrorState({ title = 'The intelligence layer hit an unexpected issue.', detail, onRetry }: { title?: string; detail: string; onRetry?: () => void }) {
  return (
    <div className="glass-card border-[var(--red)]/30 px-8 py-10 text-center">
      <p className="label-tag mb-3 text-[var(--red)]">Error</p>
      <h3 className="font-display text-lg font-medium">{title}</h3>
      <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-[var(--ink-soft)]">{detail}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn-ghost mt-6 rounded-full px-5 py-2 text-sm">
          Retry
        </button>
      )}
    </div>
  )
}

export function LoadingScreen({ label = 'Loading your workspace…' }: { label?: string }) {
  return (
    <div className="flex h-full min-h-[50vh] flex-col items-center justify-center gap-8 py-16">
      <div className="w-full max-w-[13rem]">
        <AgentPipeline compact />
      </div>
      <p className="label-tag text-[var(--ink-faint)]">{label}</p>
    </div>
  )
}
