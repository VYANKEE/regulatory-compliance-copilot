/**
 * Real follow-up Q&A on a specific analysis -- wired to the new
 * POST /analysis/{id}/ask endpoint (backend/app/agents/followup_agent.py).
 * Grounded in the actual retrieved RBI clauses for each question, not a
 * generic chatbot -- see that file's docstring for the full reasoning.
 *
 * Conversation history lives in this component's state only (not
 * persisted server-side yet -- a documented, deliberate MVP scope, see
 * the backend agent's docstring). Refreshing the page clears it.
 */
import { useEffect, useRef, useState } from 'react'
import { Send, Sparkles } from 'lucide-react'
import { askFollowUp, type FindingOut } from '../../lib/api'

interface Message {
  role: 'user' | 'assistant'
  text: string
  citations?: string[]
  isError?: boolean
}

export function FollowUpChat({ threadId, findings }: { threadId: string; findings: FindingOut[] }) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [asking, setAsking] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, asking])

  const firstGap = findings.find((f) => f.status === 'Not Met') ?? findings.find((f) => f.status === 'Partial')
  const examplePrompts = [
    firstGap ? `Why was "${firstGap.requirement}" considered ${firstGap.status.toLowerCase()}?` : 'What does this circular require overall?',
    'What does DLG mean in this context?',
    'What should we prioritize fixing first?',
  ]

  async function send(question: string) {
    const q = question.trim()
    if (!q || asking) return
    setMessages((m) => [...m, { role: 'user', text: q }])
    setInput('')
    setAsking(true)
    try {
      const res = await askFollowUp(threadId, q)
      setMessages((m) => [...m, { role: 'assistant', text: res.answer, citations: res.citations }])
    } catch (err: any) {
      const detail = err?.response?.data?.detail ?? 'Could not get an answer. Please try again.'
      setMessages((m) => [...m, { role: 'assistant', text: detail, isError: true }])
    } finally {
      setAsking(false)
    }
  }

  return (
    <div className="glass-card p-6">
      <div className="mb-4 flex items-center gap-2">
        <Sparkles size={16} className="text-[var(--signal)]" />
        <p className="label-tag text-[var(--ink-faint)]">Ask a follow-up</p>
      </div>

      {messages.length === 0 && (
        <div className="mb-4 flex flex-wrap gap-2">
          {examplePrompts.map((p) => (
            <button
              key={p}
              onClick={() => send(p)}
              className="label-tag rounded-full border border-[var(--border)] px-3 py-1.5 text-left text-[var(--ink-soft)] transition-colors hover:border-[var(--border-strong)] hover:text-[var(--ink)]"
            >
              {p}
            </button>
          ))}
        </div>
      )}

      {messages.length > 0 && (
        <div ref={scrollRef} className="mb-4 max-h-96 space-y-4 overflow-y-auto pr-1">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className="max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed"
                style={
                  m.role === 'user'
                    ? { background: 'rgba(84,232,178,0.12)', border: '1px solid var(--border-signal)' }
                    : m.isError
                      ? { background: 'rgba(226,104,92,0.08)', border: '1px solid rgba(226,104,92,0.3)' }
                      : { background: 'var(--surface)', border: '1px solid var(--border)' }
                }
              >
                <p className="whitespace-pre-wrap">{m.text}</p>
                {m.citations && m.citations.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5 border-t border-[var(--border)] pt-2">
                    {m.citations.map((c) => (
                      <span key={c} className="font-mono-ui rounded bg-white/5 px-1.5 py-0.5 text-[10px] text-[var(--ink-faint)]">
                        {c}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          {asking && (
            <div className="flex justify-start">
              <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] px-4 py-2.5">
                <span className="flex gap-1">
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[var(--ink-faint)] [animation-delay:-0.3s]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[var(--ink-faint)] [animation-delay:-0.15s]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[var(--ink-faint)]" />
                </span>
              </div>
            </div>
          )}
        </div>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault()
          send(input)
        }}
        className="field flex items-center gap-3 rounded-full px-4 py-2.5"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Why was this considered a gap?"
          className="w-full bg-transparent text-sm outline-none"
        />
        <button
          type="submit"
          disabled={asking || !input.trim()}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--signal)] text-[#04120c] transition disabled:opacity-40"
        >
          <Send size={14} />
        </button>
      </form>
      <p className="label-tag mt-3 text-[var(--ink-faint)]">
        Grounded in RBI clauses retrieved for each question, not a general-purpose chatbot.
      </p>
    </div>
  )
}
