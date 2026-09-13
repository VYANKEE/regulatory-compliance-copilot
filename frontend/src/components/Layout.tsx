import type { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { History, Settings } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { Logo } from './marketing/Logo'

/** App-shell chrome for the authenticated product. */
export function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth()
  const location = useLocation()

  const navItem = (to: string, label: string) => (
    <Link
      to={to}
      className={`label-tag rounded-full px-3.5 py-1.5 transition-colors ${
        location.pathname === to ? 'bg-[var(--surface-strong)] text-[var(--ink)]' : 'text-[var(--ink-soft)] hover:text-[var(--ink)]'
      }`}
    >
      {label}
    </Link>
  )

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-10 border-b border-[var(--border)] bg-[var(--bg)]/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <Link to="/app" className="text-[var(--ink)]">
            <Logo size="sm" />
          </Link>
          <nav className="hidden items-center gap-1 sm:flex">
            {navItem('/app', 'Dashboard')}
            {navItem('/app/new', 'New Analysis')}
            {navItem('/app/history', 'History')}
          </nav>
          {user && (
            <div className="flex items-center gap-2 text-sm">
              <Link to="/app/history" className="rounded-full p-2 text-[var(--ink-soft)] transition hover:bg-[var(--surface-strong)] hover:text-[var(--ink)] sm:hidden">
                <History size={16} />
              </Link>
              <Link to="/app/settings" className="rounded-full p-2 text-[var(--ink-soft)] transition hover:bg-[var(--surface-strong)] hover:text-[var(--ink)]">
                <Settings size={16} />
              </Link>
              <span className="label-tag hidden text-[var(--ink-faint)] md:inline">{user.email}</span>
              <button onClick={() => logout()} className="btn-ghost rounded-full px-3.5 py-1.5 text-sm">
                Sign out
              </button>
            </div>
          )}
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-6 py-10">{children}</main>
    </div>
  )
}
