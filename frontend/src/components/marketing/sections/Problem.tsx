import { Reveal, RevealGroup, RevealItem } from '../Reveal'

const OLD_STEPS = ['Documents', 'Manual reading', 'Spreadsheets', 'Multiple teams', 'Email threads', 'Manual verification', 'Delayed decision']

export function Problem() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-32 text-center">
      <Reveal className="mx-auto flex flex-col items-center">
        <span className="label-tag">The problem</span>
        <h2 className="font-display mx-auto mt-4 max-w-2xl text-3xl font-medium leading-tight sm:text-4xl">
          Every bank, NBFC and fintech carries the same weight: hundreds of RBI circulars, and no
          reliable way to know what a new one actually changes.
        </h2>
      </Reveal>

      <RevealGroup className="mt-16 flex flex-wrap items-center justify-center gap-x-2 gap-y-4" stagger={0.06}>
        {OLD_STEPS.map((step, i) => (
          <RevealItem key={step} className="flex items-center gap-2">
            <span className="label-tag rounded-full border border-[var(--border)] bg-[var(--surface)] px-4 py-2 text-[var(--ink-soft)] opacity-70 line-through decoration-[var(--red)]/60">
              {step}
            </span>
            {i < OLD_STEPS.length - 1 && <span className="text-[var(--ink-faint)]">→</span>}
          </RevealItem>
        ))}
      </RevealGroup>

      <Reveal delay={0.15} className="mx-auto mt-14 max-w-2xl">
        <p className="font-display text-2xl leading-snug text-[var(--ink-soft)] sm:text-3xl">
          What if the entire process could <span className="text-gradient not-italic">think</span> and
          still leave the final call to a person?
        </p>
      </Reveal>
    </section>
  )
}
