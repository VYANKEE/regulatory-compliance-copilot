import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileText, UploadCloud } from 'lucide-react'
import { startAnalysis, uploadPolicy } from '../lib/api'
import { MagneticButton } from '../components/marketing/MagneticButton'
import { Reveal } from '../components/marketing/Reveal'
import { AgentPipeline, type AgentRunState } from '../components/marketing/AgentPipeline'

// Abhi corpus me sirf ek "current" circular hai (baaki 3 repealed hain,
// diff/impact ke liye reference ke taur pe use hote hain) -- dropdown me
// wahi default hai, par free-text override allow hai future circulars ke
// liye (naya circular corpus me add hone pe koi frontend change nahi
// chahiye).
const KNOWN_CIRCULARS = ['RBI/2025-26/36']

export function NewAnalysisPage() {
  const navigate = useNavigate()
  const [circularRef, setCircularRef] = useState(KNOWN_CIRCULARS[0])
  const [customCircular, setCustomCircular] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [step, setStep] = useState<'idle' | 'uploading' | 'analyzing'>('idle')
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!file) {
      setError('Please choose a policy PDF to upload.')
      return
    }
    setError(null)
    setSubmitting(true)
    try {
      setStep('uploading')
      const { policy_document_id } = await uploadPolicy(file)

      setStep('analyzing')
      const result = await startAnalysis(circularRef, policy_document_id)

      navigate(`/app/threads/${result.thread_id}`)
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Something went wrong. Please try again.')
      setSubmitting(false)
      setStep('idle')
    }
  }

  const submitStates: Record<string, AgentRunState> | undefined =
    step === 'uploading'
      ? { supervisor: 'queued', retrieval: 'idle', diff: 'idle', impact: 'idle', verifier: 'idle', report: 'idle', human: 'idle' }
      : step === 'analyzing'
        ? { supervisor: 'running', retrieval: 'running', diff: 'queued', impact: 'queued', verifier: 'idle', report: 'idle', human: 'idle' }
        : undefined

  return (
    <div className="mx-auto max-w-xl">
      <Reveal>
        <p className="label-tag mb-1 text-[var(--ink-faint)]">Ask Niriksh</p>
        <h1 className="font-display text-3xl font-medium">New Analysis</h1>
        <p className="mt-2 text-sm leading-relaxed text-[var(--ink-soft)]">
          Upload your internal policy document and pick the circular to check it against. The full
          six-agent pipeline runs on submit.
        </p>
      </Reveal>

      <Reveal delay={0.1}>
        <form onSubmit={handleSubmit} className="glass-card mt-8 space-y-6 p-6">
          <div>
            <label className="label-tag mb-2 block">Circular</label>
            {!customCircular ? (
              <select
                value={circularRef}
                onChange={(e) => setCircularRef(e.target.value)}
                className="field w-full rounded-lg px-3.5 py-2.5 text-sm"
              >
                {KNOWN_CIRCULARS.map((c) => (
                  <option key={c} value={c} className="bg-[#0d0f12]">
                    {c}
                  </option>
                ))}
              </select>
            ) : (
              <input
                value={circularRef}
                onChange={(e) => setCircularRef(e.target.value)}
                placeholder="e.g. RBI/2025-26/36"
                className="field w-full rounded-lg px-3.5 py-2.5 text-sm"
              />
            )}
            <button
              type="button"
              onClick={() => setCustomCircular((v) => !v)}
              className="label-tag mt-2 text-[var(--signal)]"
            >
              {customCircular ? 'Choose from list instead' : 'Enter a different circular ref'}
            </button>
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between gap-3">
              <label className="label-tag">Policy document</label>
              <a href="/api/policies/sample" className="label-tag text-[var(--signal)]">
                Download a sample
              </a>
            </div>
            <label
              onDragOver={(e) => {
                e.preventDefault()
                setDragOver(true)
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => {
                e.preventDefault()
                setDragOver(false)
                const f = e.dataTransfer.files?.[0]
                if (f) setFile(f)
              }}
              className="flex cursor-pointer flex-col items-center gap-3 rounded-xl border border-dashed px-6 py-10 text-center transition-colors"
              style={{
                borderColor: dragOver ? 'var(--signal)' : 'var(--border)',
                background: dragOver ? 'rgba(84,232,178,0.05)' : 'transparent',
              }}
            >
              <input type="file" accept="application/pdf" onChange={(e) => setFile(e.target.files?.[0] ?? null)} className="hidden" />
              {file ? (
                <>
                  <FileText size={28} className="text-[var(--signal)]" />
                  <span className="text-sm font-medium">{file.name}</span>
                  <span className="label-tag text-[var(--ink-faint)]">{(file.size / 1024).toFixed(0)} KB · click to replace</span>
                </>
              ) : (
                <>
                  <UploadCloud size={28} className="text-[var(--ink-faint)]" />
                  <span className="text-sm font-medium">Drop your policy PDF, or click to browse</span>
                  <span className="label-tag text-[var(--ink-faint)]">No policy handy? Use the sample above.</span>
                </>
              )}
            </label>
          </div>

          {error && <p className="text-sm text-[var(--red)]">{error}</p>}

          <MagneticButton type="submit" disabled={submitting} className="w-full">
            {step === 'uploading' && 'Uploading policy…'}
            {step === 'analyzing' && 'Starting analysis…'}
            {step === 'idle' && 'Start Analysis'}
          </MagneticButton>
        </form>
      </Reveal>

      {submitStates && (
        <Reveal delay={0.1} className="glass-card mt-4 p-5">
          <p className="label-tag mb-4 text-[var(--ink-faint)]">Kicking off the pipeline</p>
          <AgentPipeline compact states={submitStates} />
        </Reveal>
      )}
    </div>
  )
}
