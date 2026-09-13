import { Link } from 'react-router-dom'
import { Reveal } from '../Reveal'
import { MagneticButton } from '../MagneticButton'

export function FinalCTA() {
  return (
    <section className="relative mx-auto max-w-6xl px-6 py-40 text-center">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10"
        style={{
          background: 'radial-gradient(ellipse 700px 400px at 50% 50%, rgba(84,232,178,0.10), transparent 70%)',
        }}
      />
      <Reveal>
        <p className="font-display mx-auto max-w-3xl text-4xl font-medium leading-tight sm:text-6xl">
          Compliance shouldn't wait for humans to catch up.
        </p>
      </Reveal>
      <Reveal delay={0.15} className="mt-12">
        <MagneticButton className="text-base">
          <Link to="/signup" className="contents">
            Enter Niriksh →
          </Link>
        </MagneticButton>
      </Reveal>
    </section>
  )
}
