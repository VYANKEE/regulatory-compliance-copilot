/**
 * Axios client -- har request pe automatically current Firebase user ka
 * fresh ID token attach karta hai (Authorization: Bearer <token>).
 *
 * Important concept: `getIdToken()` bina force-refresh ke bhi call karna
 * safe hai -- Firebase SDK khud hi token expiry (1 hour) track karta hai
 * aur zaroorat pade to silently refresh kar deta hai. Isliye humein khud
 * kabhi token refresh logic likhne ki zaroorat nahi.
 */
import axios from 'axios'
import { auth } from './firebase'

export const api = axios.create({
  baseURL: '/api',
})

api.interceptors.request.use(async (config) => {
  const user = auth.currentUser
  if (user) {
    const token = await user.getIdToken()
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export interface FindingOut {
  id: string
  requirement: string
  status: string
  rbi_citation: string
  explanation: string
  suggested_policy_change: string
}

export interface ThreadSummary {
  id: string
  circular_ref: string
  status: string
  created_at: string
  updated_at: string
}

export interface ThreadOut extends ThreadSummary {
  report: string
  findings: FindingOut[]
}

export interface StartAnalysisResponse {
  thread_id: string
  status: string
  approval_pending: boolean
  draft_report: string | null
  verified_findings_count: number | null
}

export async function uploadPolicy(file: File): Promise<{ policy_document_id: string; filename: string }> {
  const form = new FormData()
  form.append('file', file)
  const res = await api.post('/policies/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

export async function startAnalysis(circular_ref: string, policy_document_id: string): Promise<StartAnalysisResponse> {
  const res = await api.post('/analysis/start', { circular_ref, policy_document_id })
  return res.data
}

export async function approveAnalysis(threadId: string, approved: boolean, feedback = ''): Promise<ThreadOut> {
  const res = await api.post(`/analysis/${threadId}/approve`, { approved, feedback })
  return res.data
}

export async function getThread(threadId: string): Promise<ThreadOut> {
  const res = await api.get(`/analysis/${threadId}`)
  return res.data
}

export async function listThreads(): Promise<ThreadSummary[]> {
  const res = await api.get('/analysis/')
  return res.data
}

export async function deleteThread(threadId: string): Promise<void> {
  await api.delete(`/analysis/${threadId}`)
}

export interface AskResponse {
  answer: string
  citations: string[]
}

export async function askFollowUp(threadId: string, question: string): Promise<AskResponse> {
  const res = await api.post(`/analysis/${threadId}/ask`, { question })
  return res.data
}
