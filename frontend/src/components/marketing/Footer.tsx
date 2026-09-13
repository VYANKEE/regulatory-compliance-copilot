import { Logo } from './Logo'

export function Footer() {
  return (
    <footer className="border-t border-[var(--border)] px-6 py-12">
      <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-6 sm:flex-row sm:items-center">
        <div>
          <Logo size="sm" />
          <p className="label-tag mt-3 max-w-xs text-[var(--ink-faint)]">
            AI compliance intelligence: an agentic pipeline for regulatory impact analysis.
          </p>
        </div>
        <p className="label-tag text-[var(--ink-faint)]">Built on RBI Digital Lending Directions, 2025</p>
      </div>
    </footer>
  )
}
