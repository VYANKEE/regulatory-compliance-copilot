import { Reveal } from '../Reveal'

// "Impact + verification", not "confidence" -- the backend has no confidence score.
const STEPS = ['AI analysis', 'Impact + verification', 'Human review', 'Approve / Reject']

export function HumanInLoop() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-32">
      <div className="grid grid-cols-1 gap-16 lg:grid-cols-2 lg:items-center">
        <Reveal>
          <span className="label-tag">Product philosophy, not a disclaimer</span>
          <h2 className="font-display mt-4 text-4xl font-medium leading-tight sm:text-5xl">
            The AI does not sign off on anything.
          </h2>
          <p className="mt-6 max-w-md leading-relaxed text-[var(--ink-soft)]">
            Every analysis reaches a pause before it becomes a record. A person reads the memo, the
            findings, and the citations behind them, and decides. Reject it, and the finding is
            withheld, not silently overridden.
          </p>
        </Reveal>

        <Reveal delay={0.15}>
          <div className="glass-card p-8">
            {STEPS.map((step, i) => (
              <div key={step} className="flex items-center gap-4">
                <div className="flex flex-col items-center">
                  <span
                    className="flex h-9 w-9 items-center justify-center rounded-full border font-mono-ui text-xs"
                    style={{
                      borderColor: i === 2 ? 'var(--border-signal)' : 'var(--border)',
                      color: i === 2 ? 'var(--signal)' : 'var(--ink-soft)',
                      background: i === 2 ? 'rgba(84,232,178,0.08)' : 'transparent',
                    }}
                  >
                    {i + 1}
                  </span>
                  {i < STEPS.length - 1 && <span className="my-1 h-8 w-px bg-[var(--border)]" />}
                </div>
                <span className={`pb-8 text-sm ${i === 2 ? 'font-semibold text-[var(--ink)]' : 'text-[var(--ink-soft)]'}`}>
                  {step}
                </span>
              </div>
            ))}
          </div>
        </Reveal>
      </div>
    </section>
  )
}
