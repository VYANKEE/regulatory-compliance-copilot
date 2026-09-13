/**
 * Firebase client init.
 *
 * Important concept: ye keys (apiKey, authDomain, etc.) SECRET nahi hain --
 * Firebase client config public hai by design (browser me hamesha visible
 * rehta hai, kisi bhi website ka "view source" karke dikh jaata hai).
 * Asli security Firebase Console ke "Authorized domains" + backend ke
 * `verify_firebase_token` (ID token cryptographically verify karta hai) se
 * aati hai, config chhupane se nahi. Isliye ye values `.env` me VITE_
 * prefix ke saath (frontend build-time env vars) rakhna safe hai.
 */
import { initializeApp } from 'firebase/app'
import { GoogleAuthProvider, getAuth } from 'firebase/auth'

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
}

export const firebaseApp = initializeApp(firebaseConfig)
export const auth = getAuth(firebaseApp)
export const googleProvider = new GoogleAuthProvider()
