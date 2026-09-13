/**
 * NIRIKSH wordmark. Deliberately typographic, not a shield/checkmark icon --
 * the "mark" is a single signal-colored dot standing in for the aperture /
 * observation point the name refers to (Niriksh = to observe closely).
 */
export function Logo({ size = 'md', showWord = true }: { size?: 'sm' | 'md' | 'lg'; showWord?: boolean }) {
  const dims = { sm: 'text-base', md: 'text-xl', lg: 'text-3xl md:text-5xl' }[size]
  return (
    <span className={`inline-flex items-center gap-2 font-display font-semibold tracking-tight ${dims}`}>
      <span className="relative inline-flex h-[0.5em] w-[0.5em] items-center justify-center">
        <span className="absolute inset-0 rounded-full border border-[var(--signal)]/50" />
        <span className="h-[0.22em] w-[0.22em] rounded-full bg-[var(--signal)] shadow-[0_0_12px_2px_rgba(84,232,178,0.55)]" />
      </span>
      <span>
        NIRIKSH
        {showWord && <span className="sr-only">: AI Compliance Intelligence</span>}
      </span>
    </span>
  )
}
