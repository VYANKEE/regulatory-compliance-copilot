/**
 * Single source of truth for the agent pipeline shown across the site
 * (landing hero diagram, "How It Works", the Agents section, and later the
 * live-run experience). Deliberately mirrors the REAL backend pipeline in
 * backend/app/agents/{supervisor,graph}.py -- no invented agents, no
 * fabricated capabilities. If the backend pipeline changes, update this
 * file to match rather than letting the UI drift from reality.
 */
export interface AgentSpec {
  id: string
  name: string
  role: string
  receives: string
  analyzes: string
  tools: string
  produces: string
  talksTo: string
}

export const AGENTS: AgentSpec[] = [
  {
    id: 'supervisor',
    name: 'Supervisor',
    role: 'Orchestrates the analysis across every regulatory topic in the circular.',
    receives: 'A circular reference and an uploaded internal policy document.',
    analyzes: 'Which of the six fixed regulatory topics apply, and fans them out concurrently.',
    tools: 'LangGraph StateGraph, ThreadPoolExecutor concurrency, Postgres-backed checkpointing.',
    produces: 'A coordinated run of Retrieval → Diff → Impact per topic, then Verification.',
    talksTo: 'Retrieval, Diff, Impact — and pauses for Human Review before finishing.',
  },
  {
    id: 'retrieval',
    name: 'Retrieval Agent',
    role: 'Finds the exact clauses relevant to a topic across the circular corpus.',
    receives: 'A regulatory topic (e.g. "Cooling-off period for digital loans").',
    analyzes: 'Current and repealed circular text, via similarity search over embedded clauses.',
    tools: 'A hand-written cosine-similarity vector store (NVIDIA NIM embeddings).',
    produces: 'The current and repealed clause chunks most relevant to that topic.',
    talksTo: 'Diff Agent and Impact Agent, who both consume its retrieved context.',
  },
  {
    id: 'diff',
    name: 'Diff Agent',
    role: 'Determines what changed between the repealed and current circular.',
    receives: 'Current + repealed clause chunks for one topic, from Retrieval.',
    analyzes: 'What was added, removed, or superseded for that requirement.',
    tools: 'Gemini / NVIDIA NIM generation, a strict "no fabricated citations" prompt.',
    produces: 'A structured diff narrative per topic, cited to real chunk IDs.',
    talksTo: 'Report Agent, which assembles its output into the final memo.',
  },
  {
    id: 'impact',
    name: 'Impact Agent',
    role: 'Checks whether the uploaded policy actually satisfies each requirement.',
    receives: 'Current clauses for a topic, plus the full uploaded policy text.',
    analyzes: 'Met / Partial / Not Met status against each current requirement.',
    tools: 'Gemini / NVIDIA NIM generation, structured JSON output (not free text).',
    produces: 'Raw findings — one per requirement, each with a citation and rationale.',
    talksTo: 'Verifier Agent, who independently re-checks every finding it produces.',
  },
  {
    id: 'verifier',
    name: 'Verifier Agent',
    role: 'The independent check — nothing reaches a human unless it is grounded.',
    receives: 'Every raw finding the Impact Agent produced, across all topics.',
    analyzes: "Whether each finding's claim is actually supported by its cited clause — read fresh from the corpus, not reused from Impact Agent's context.",
    tools: 'A separate grounding-check LLM call per finding, plus deterministic citation-normalization.',
    produces: 'Only the findings that survive independent verification; the rest are discarded, not shown.',
    talksTo: 'Report Agent, and ultimately the human reviewer.',
  },
  {
    id: 'report',
    name: 'Report Agent',
    role: 'Compiles the final memo — deliberately not an LLM call.',
    receives: 'Verified findings and topic diffs only.',
    analyzes: 'Nothing — it templates, it does not generate. No new hallucination surface at the last step.',
    tools: 'Deterministic Markdown templating.',
    produces: 'The Compliance Impact Memo a human reviewer signs off on.',
    talksTo: 'The Human Review step.',
  },
]

export const HUMAN_REVIEW = {
  id: 'human',
  name: 'Human Review',
  role: 'The analysis pauses here. Nothing is final until a person approves it.',
}
