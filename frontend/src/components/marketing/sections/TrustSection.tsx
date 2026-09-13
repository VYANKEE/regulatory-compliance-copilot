import { Reveal, RevealGroup, RevealItem } from '../Reveal'

// No fake certifications/logos/uptime numbers -- only real architecture properties.
const PRINCIPLES = [
  { title: 'Traceability', detail: 'Every finding carries the exact clause it was checked against.' },
  { title: 'Independent verification', detail: 'A separate agent re-checks each claim before it reaches a person.' },
  { title: 'Explainability', detail: 'Findings are structured (requirement, status, citation, rationale), never a black-box summary.' },
  { title: 'Human oversight', detail: 'No memo is final without an explicit human approval decision.' },
  { title: 'Auditability', detail: 'Every analysis, approval and rejection is written to an audit log.' },
  { title: 'Structured reasoning', detail: 'Each pipeline stage has one job: retrieve, diff, assess, verify, report.' },
]

export function TrustSection() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-32">
      <Reveal>
        <span className="label-tag">Built to be checked, not just trusted</span>
        <h2 className="font-display mt-4 max-w-2xl text-4xl font-medium leading-tight sm:text-5xl">
          A compliance system should be as auditable as the compliance it checks.
        </h2>
      </Reveal>

      <RevealGroup className="mt-16 grid grid-cols-1 gap-px overflow-hidden rounded-2xl border border-[var(--border)] sm:grid-cols-2 lg:grid-cols-3" stagger={0.05}>
        {PRINCIPLES.map((p) => (
          <RevealItem key={p.title}>
            <div className="h-full bg-[var(--bg-raised)] p-7">
              <h3 className="text-base font-semibold">{p.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-[var(--ink-soft)]">{p.detail}</p>
            </div>
          </RevealItem>
        ))}
      </RevealGroup>
    </section>
  )
}
