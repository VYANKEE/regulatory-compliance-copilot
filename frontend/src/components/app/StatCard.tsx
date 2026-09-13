export function StatCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="glass-card p-5">
      <p className="label-tag text-[var(--ink-faint)]">{label}</p>
      <p className="font-display mt-2 text-3xl font-medium">{value}</p>
      {hint && <p className="mt-1 text-xs text-[var(--ink-soft)]">{hint}</p>}
    </div>
  )
}
