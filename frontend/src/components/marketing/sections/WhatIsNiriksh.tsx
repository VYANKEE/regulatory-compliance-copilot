import { Reveal } from '../Reveal'

const QA = [
  {
    q: 'What problem does it solve?',
    a: 'Turning a new regulatory circular into a concrete answer usually took a compliance officer days of manual cross-referencing: what changed, and whether the policy already covered it.',
  },
  {
    q: 'Why do traditional workflows fail?',
    a: "They rely on one person reading dense legal text end to end, remembering what the last version said, and manually matching it against an internal policy document. It doesn't scale, and nothing forces a citation for every claim.",
  },
  {
    q: 'What does Niriksh automate?',
    a: 'Retrieving the exact relevant clauses, diffing old versus new, checking your policy against each requirement, and independently verifying every resulting claim against source text before a human ever sees it.',
  },
  {
    q: 'Where does the human stay in control?',
    a: 'Nothing is final until a person reviews the memo and explicitly approves or rejects it. Niriksh prepares the case. It does not make the compliance decision.',
  },
]

export function WhatIsNiriksh() {
  return (
    <section id="what-is-niriksh" className="mx-auto max-w-6xl px-6 py-32">
      <Reveal>
        <span className="label-tag">What is Niriksh</span>
        <h2 className="font-display mt-4 max-w-3xl text-4xl font-medium leading-tight sm:text-5xl">
          An agentic reading of every circular you're responsible for,
          <span className="text-[var(--ink-soft)]"> with a citation for every sentence.</span>
        </h2>
      </Reveal>

      <div className="mt-20 grid grid-cols-1 gap-x-12 gap-y-14 md:grid-cols-2">
        {QA.map((item, i) => (
          <Reveal key={item.q} delay={i * 0.08}>
            <p className="font-mono-ui text-xs text-[var(--signal)]">{String(i + 1).padStart(2, '0')}</p>
            <h3 className="font-display mt-3 text-xl font-medium">{item.q}</h3>
            <p className="mt-3 leading-relaxed text-[var(--ink-soft)]">{item.a}</p>
          </Reveal>
        ))}
      </div>
    </section>
  )
}
