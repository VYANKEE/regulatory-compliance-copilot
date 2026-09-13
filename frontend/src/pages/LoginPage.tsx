import { motion } from 'framer-motion'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AgentPipeline } from '../components/marketing/AgentPipeline'
import { Logo } from '../components/marketing/Logo'
import { MagneticButton } from '../components/marketing/MagneticButton'
import { useAuth } from '../contexts/AuthContext'

const INSIGHTS = [
  'Every finding is checked against source text before it reaches you.',
  'Six regulatory topics analyzed concurrently, not one at a time.',
  'Nothing is final until a human reviewer approves it.',
  'Report Agent compiles the memo deterministically: no generation, no drift.',
]

export function LoginPage() {
  const { login, loginWithEmail } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [insight, setInsight] = useState(0)

  useState(() => {
    const t = setInterval(() => setInsight((i) => (i + 1) % INSIGHTS.length), 4000)
    return () => clearInterval(t)
  })

  async function handleGoogle() {
    setError('')
    setBusy(true)
    try {
      await login()
      navigate('/app')
    } catch {
      setError('Could not sign in with Google. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  async function handleEmailSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      await loginWithEmail(email, password)
      navigate('/app')
    } catch {
      setError('Incorrect email or password.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="grid min-h-screen grid-cols-1 lg:grid-cols-2">
      {/* left: brand + living visualization */}
      <div className="relative hidden overflow-hidden border-r border-[var(--border)] bg-[var(--bg-raised)] p-12 lg:flex lg:flex-col lg:justify-between">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              'radial-gradient(ellipse 600px 500px at 20% 10%, rgba(84,232,178,0.14), transparent 60%), radial-gradient(ellipse 500px 500px at 90% 90%, rgba(82,199,232,0.10), transparent 60%)',
          }}
        />
        <Link to="/" className="relative text-[var(--ink)]">
          <Logo />
        </Link>

        <div className="relative">
          <p className="font-display max-w-md text-3xl font-medium leading-tight">
            Your compliance layer, continuously thinking.
          </p>
          <div className="mt-10 max-w-xs">
            <AgentPipeline compact />
          </div>
        </div>

        <motion.p key={insight} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="label-tag relative max-w-sm text-[var(--ink-soft)]">
          {INSIGHTS[insight]}
        </motion.p>
      </div>

      {/* right: form */}
      <div className="flex flex-col items-center justify-center px-6 py-16">
        <div className="w-full max-w-sm">
          <div className="mb-10 lg:hidden">
            <Logo size="sm" />
          </div>
          <h1 className="font-display text-3xl font-medium">Welcome back</h1>
          <p className="mt-2 text-sm text-[var(--ink-soft)]">Sign in to continue to your workspace.</p>

          <button
            onClick={handleGoogle}
            disabled={busy}
            className="btn-ghost mt-8 flex w-full items-center justify-center gap-3 rounded-full py-3 text-sm font-medium disabled:opacity-50"
          >
            <GoogleMark />
            Continue with Google
          </button>

          <div className="my-7 flex items-center gap-4">
            <div className="h-px flex-1 bg-[var(--border)]" />
            <span className="label-tag text-[var(--ink-faint)]">or</span>
            <div className="h-px flex-1 bg-[var(--border)]" />
          </div>

          <form onSubmit={handleEmailSubmit} className="space-y-4">
            <div>
              <label className="label-tag mb-2 block">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="field w-full rounded-lg px-4 py-3 text-sm"
                placeholder="you@organization.com"
              />
            </div>
            <div>
              <div className="mb-2 flex items-center justify-between">
                <label className="label-tag">Password</label>
                <span className="label-tag cursor-not-allowed text-[var(--ink-faint)]" title="Password reset is not yet wired to the backend">
                  Forgot password?
                </span>
              </div>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="field w-full rounded-lg px-4 py-3 text-sm"
                placeholder="••••••••"
              />
            </div>

            {error && <p className="text-sm text-[var(--red)]">{error}</p>}

            <MagneticButton type="submit" disabled={busy} className="mt-2 w-full">
              {busy ? 'Signing in…' : 'Sign in'}
            </MagneticButton>
          </form>

          <p className="mt-8 text-center text-sm text-[var(--ink-soft)]">
            New to Niriksh?{' '}
            <Link to="/signup" className="font-medium text-[var(--signal)]">
              Create an account
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

function GoogleMark() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18">
      <path fill="#4285F4" d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.9c1.7-1.57 2.7-3.87 2.7-6.62z" />
      <path fill="#34A853" d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.9-2.26c-.8.54-1.84.86-3.06.86-2.35 0-4.34-1.59-5.05-3.72H.96v2.33A9 9 0 0 0 9 18z" />
      <path fill="#FBBC05" d="M3.95 10.7A5.4 5.4 0 0 1 3.67 9c0-.59.1-1.17.28-1.7V4.97H.96A9 9 0 0 0 0 9c0 1.45.35 2.83.96 4.03z" />
      <path fill="#EA4335" d="M9 3.58c1.32 0 2.51.46 3.44 1.35l2.58-2.58C13.46.89 11.43 0 9 0A9 9 0 0 0 .96 4.97L3.95 7.3C4.66 5.17 6.65 3.58 9 3.58z" />
    </svg>
  )
}
