/**
 * Scoped deliberately to what's real. The backend's User model
 * (db/models.py) only stores id / email / display_name via Firebase --
 * there is no organization, workspace, notification-preference, AI-config
 * or connected-systems concept anywhere in this system. Rather than fake
 * toggles for those, they're shown as clearly-labeled "not configured"
 * rows -- honest per the project's no-fabricated-data rule, and it's an
 * easy, correct place to extend later if those features get built.
 */
import { useState } from 'react'
import { sendPasswordResetEmail, updateProfile } from 'firebase/auth'
import { useAuth } from '../contexts/AuthContext'
import { auth } from '../lib/firebase'
import { Reveal } from '../components/marketing/Reveal'
import { MagneticButton } from '../components/marketing/MagneticButton'

const NOT_CONFIGURED = ['Organization', 'Workspace', 'Notifications', 'AI configuration', 'Connected systems']

export function SettingsPage() {
  const { user, logout } = useAuth()
  const [name, setName] = useState(user?.displayName ?? '')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [resetSent, setResetSent] = useState(false)

  const isPasswordUser = user?.providerData.some((p) => p.providerId === 'password')

  async function handleSave() {
    if (!user) return
    setSaving(true)
    setSaved(false)
    try {
      await updateProfile(user, { displayName: name.trim() })
      setSaved(true)
    } finally {
      setSaving(false)
    }
  }

  async function handleReset() {
    if (!user?.email) return
    await sendPasswordResetEmail(auth, user.email)
    setResetSent(true)
  }

  return (
    <div className="mx-auto max-w-2xl">
      <Reveal>
        <p className="label-tag mb-1 text-[var(--ink-faint)]">Account</p>
        <h1 className="font-display text-3xl font-medium">Settings</h1>
      </Reveal>

      <Reveal delay={0.05} className="glass-card mt-8 p-6">
        <p className="label-tag mb-5 text-[var(--signal)]">Profile</p>
        <div className="space-y-4">
          <div>
            <label className="label-tag mb-2 block">Display name</label>
            <input value={name} onChange={(e) => setName(e.target.value)} className="field w-full rounded-lg px-3.5 py-2.5 text-sm" />
          </div>
          <div>
            <label className="label-tag mb-2 block">Email</label>
            <input value={user?.email ?? ''} disabled className="field w-full rounded-lg px-3.5 py-2.5 text-sm opacity-60" />
          </div>
          <div className="flex items-center gap-3">
            <MagneticButton onClick={handleSave} disabled={saving} className="!px-5 !py-2.5 text-sm">
              {saving ? 'Saving…' : 'Save changes'}
            </MagneticButton>
            {saved && <span className="label-tag text-[var(--signal)]">Saved</span>}
          </div>
        </div>
      </Reveal>

      <Reveal delay={0.1} className="glass-card mt-4 p-6">
        <p className="label-tag mb-5 text-[var(--signal)]">Security</p>
        {isPasswordUser ? (
          <div className="flex items-center gap-3">
            <button onClick={handleReset} className="btn-ghost rounded-full px-4 py-2 text-sm">
              Send password reset email
            </button>
            {resetSent && <span className="label-tag text-[var(--signal)]">Sent</span>}
          </div>
        ) : (
          <p className="text-sm text-[var(--ink-soft)]">You're signed in with Google. Password reset is managed by your Google account.</p>
        )}
        <button onClick={() => logout()} className="label-tag mt-5 text-[var(--red)]">
          Sign out of Niriksh
        </button>
      </Reveal>

      <Reveal delay={0.15} className="glass-card mt-4 p-6">
        <p className="label-tag mb-4 text-[var(--ink-faint)]">Not yet configured</p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {NOT_CONFIGURED.map((item) => (
            <div key={item} className="rounded-lg border border-dashed border-[var(--border)] px-3 py-3 text-center">
              <p className="text-xs text-[var(--ink-faint)]">{item}</p>
            </div>
          ))}
        </div>
      </Reveal>
    </div>
  )
}
