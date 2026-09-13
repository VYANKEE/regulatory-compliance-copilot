/**
 * Registration, redesigned as a short onboarding moment rather than a form
 * dump. Deliberately only TWO real steps -- Identity, then Ready -- because
 * that's all the backend actually has a use for (User row = id, email,
 * display_name via Firebase). An "Organization / Compliance Environment /
 * Workspace" wizard would look premium but collect fields nothing reads;
 * per the project's no-fake-data rule, this stays honest instead.
 */
import { AnimatePresence, motion } from 'framer-motion'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AgentPipeline } from '../components/marketing/AgentPipeline'
import { Logo } from '../components/marketing/Logo'
import { MagneticButton } from '../components/marketing/MagneticButton'
import { useAuth } from '../contexts/AuthContext'

const STEPS = ['Identity', 'Ready']

export function SignupPage() {
  const { signupWithEmail, login } = useAuth()
  const navigate = useNavigate()
  const [step, setStep] = useState(0)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  function handleContinue(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    if (password.length < 6) {
      setError('Password must be at least 6 characters.')
      return
    }
    setStep(1)
  }

  async function handleCreate() {
    setBusy(true)
    setError('')
    try {
      await signupWithEmail(email, password, name)
      navigate('/app')
    } catch {
      setError('Could not create your account: that email may already be in use.')
      setStep(0)
    } finally {
      setBusy(false)
    }
  }

  async function handleGoogle() {
    setBusy(true)
    setError('')
    try {
      await login()
      navigate('/app')
    } catch {
      setError('Could not sign up with Google.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="relative flex min-h-screen flex-col items-center px-6 py-16">
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 -z-10 transition-opacity duration-700"
        style={{
          background:
            step === 0
              ? 'radial-gradient(ellipse 700px 500px at 30% 0%, rgba(84,232,178,0.10), transparent 60%)'
              : 'radial-gradient(ellipse 700px 500px at 70% 100%, rgba(82,199,232,0.14), transparent 60%)',
        }}
      />

      <Link to="/" className="mb-10 text-[var(--ink)]">
        <Logo size="sm" />
      </Link>

      {/* step indicator */}
      <div className="mb-10 flex items-center gap-3">
        {STEPS.map((label, i) => (
          <div key={label} className="flex items-center gap-3">
            <div className="flex flex-col items-center gap-1.5">
              <span
                className="flex h-8 w-8 items-center justify-center rounded-full border font-mono-ui text-xs transition-colors"
                style={{
                  borderColor: i <= step ? 'var(--border-signal)' : 'var(--border)',
                  color: i <= step ? 'var(--signal)' : 'var(--ink-faint)',
                  background: i <= step ? 'rgba(84,232,178,0.08)' : 'transparent',
                }}
              >
                {String(i + 1).padStart(2, '0')}
              </span>
              <span className="label-tag text-[var(--ink-faint)]">{label}</span>
            </div>
            {i < STEPS.length - 1 && (
              <span className="mb-5 h-px w-10" style={{ background: i < step ? 'var(--signal)' : 'var(--border)' }} />
            )}
          </div>
        ))}
      </div>

      <div className="w-full max-w-sm">
        <AnimatePresence mode="wait">
          {step === 0 && (
            <motion.div key="identity" initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -16 }} transition={{ duration: 0.35 }}>
              <h1 className="font-display text-3xl font-medium">Create your account</h1>
              <p className="mt-2 text-sm text-[var(--ink-soft)]">Start reading circulars the way they were meant to be read.</p>

              <button
                onClick={handleGoogle}
                disabled={busy}
                className="btn-ghost mt-8 w-full rounded-full py-3 text-sm font-medium disabled:opacity-50"
              >
                Continue with Google
              </button>
              <div className="my-7 flex items-center gap-4">
                <div className="h-px flex-1 bg-[var(--border)]" />
                <span className="label-tag text-[var(--ink-faint)]">or</span>
                <div className="h-px flex-1 bg-[var(--border)]" />
              </div>

              <form onSubmit={handleContinue} className="space-y-4">
                <div>
                  <label className="label-tag mb-2 block">Name</label>
                  <input value={name} onChange={(e) => setName(e.target.value)} required className="field w-full rounded-lg px-4 py-3 text-sm" placeholder="Your name" />
                </div>
                <div>
                  <label className="label-tag mb-2 block">Email</label>
                  <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required className="field w-full rounded-lg px-4 py-3 text-sm" placeholder="you@organization.com" />
                </div>
                <div>
                  <label className="label-tag mb-2 block">Password</label>
                  <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required className="field w-full rounded-lg px-4 py-3 text-sm" placeholder="At least 6 characters" />
                </div>
                {error && <p className="text-sm text-[var(--red)]">{error}</p>}
                <MagneticButton type="submit" className="mt-2 w-full">
                  Continue
                </MagneticButton>
              </form>
            </motion.div>
          )}

          {step === 1 && (
            <motion.div key="ready" initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -16 }} transition={{ duration: 0.35 }}>
              <h1 className="font-display text-3xl font-medium">You're ready, {name.split(' ')[0] || 'there'}.</h1>
              <p className="mt-2 text-sm text-[var(--ink-soft)]">Here's what starts running the moment you submit your first analysis.</p>

              <div className="glass-card mt-8 p-6">
                <AgentPipeline compact />
              </div>

              {error && <p className="mt-4 text-sm text-[var(--red)]">{error}</p>}

              <MagneticButton onClick={handleCreate} disabled={busy} className="mt-8 w-full">
                {busy ? 'Creating account…' : 'Create account'}
              </MagneticButton>
              <button onClick={() => setStep(0)} className="label-tag mt-4 w-full text-center text-[var(--ink-faint)]">
                ← Back
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        <p className="mt-8 text-center text-sm text-[var(--ink-soft)]">
          Already have an account?{' '}
          <Link to="/login" className="font-medium text-[var(--signal)]">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
