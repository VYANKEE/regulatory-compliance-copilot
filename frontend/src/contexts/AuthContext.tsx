/**
 * Auth state -- ek jagah se poore app ko pata chalta hai kaun login hai.
 *
 * Important concept: `onAuthStateChanged` Firebase ka listener hai jo
 * automatically fire hota hai jab bhi login/logout ho, YA jab page
 * refresh ho (Firebase localStorage me session persist karta hai) --
 * isliye humein khud "check if already logged in" wala logic likhne ki
 * zaroorat nahi, ye listener wahi kaam karta hai on mount.
 *
 * Google Sign-In ke saath-saath email/password bhi supported hai -- dono
 * Firebase Console me alag-alag "Sign-in method" providers ke through
 * enable hote hain, par backend ke liye farak nahi padta: dono se aakhir
 * me ek Firebase ID token hi milta hai jo `verify_firebase_token` verify
 * karta hai, provider chahe jo bhi ho.
 *
 * `signupWithEmail` now also accepts an optional displayName and sets it
 * via Firebase's own `updateProfile` -- this is a frontend-only addition
 * (Firebase client SDK profile field), it does NOT touch the backend: the
 * backend's User row already stores display_name and is populated from
 * whatever the verified Firebase token carries, so this makes that field
 * meaningful instead of always blank for email/password signups.
 */
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import {
  createUserWithEmailAndPassword,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
  updateProfile,
  type User,
} from 'firebase/auth'
import { auth, googleProvider } from '../lib/firebase'

interface AuthContextValue {
  user: User | null
  loading: boolean
  login: () => Promise<void>
  loginWithEmail: (email: string, password: string) => Promise<void>
  signupWithEmail: (email: string, password: string, displayName?: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (u) => {
      setUser(u)
      setLoading(false)
    })
    return unsubscribe
  }, [])

  async function login() {
    await signInWithPopup(auth, googleProvider)
  }

  async function loginWithEmail(email: string, password: string) {
    await signInWithEmailAndPassword(auth, email, password)
  }

  async function signupWithEmail(email: string, password: string, displayName?: string) {
    const cred = await createUserWithEmailAndPassword(auth, email, password)
    if (displayName?.trim()) {
      await updateProfile(cred.user, { displayName: displayName.trim() })
    }
  }

  async function logout() {
    await signOut(auth)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, loginWithEmail, signupWithEmail, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
