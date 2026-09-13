import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Logo } from './marketing/Logo'

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-6">
        <Logo />
        <div className="flex items-center gap-3 text-sm text-[var(--ink-soft)]">
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/10 border-t-[var(--signal)]" />
          <span className="label-tag">Connecting to your workspace…</span>
        </div>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}
