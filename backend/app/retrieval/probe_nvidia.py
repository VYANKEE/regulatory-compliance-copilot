"""One-off: har candidate embedding/chat model ko ek chhota real test call karke
dekhta hai kaunsa is account/key ke liye actually kaam kar raha hai (kyunki
/v1/models list mein saare catalog models dikhte hain, sab enabled nahi hote)."""

from dotenv import load_dotenv

load_dotenv()

from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings

EMBED_CANDIDATES = [
    "nvidia/embed-qa-4",
    "nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1",
    "nvidia/llama-3.2-nv-embedqa-1b-v1",
    "nvidia/llama-nemotron-embed-vl-1b-v2",
    "nvidia/nemotron-3-embed-1b",
    "nvidia/nv-embedqa-mistral-7b-v2",
    "snowflake/arctic-embed-l",
]

CHAT_CANDIDATES = [
    "nvidia/llama3-chatqa-1.5-70b",
    "nvidia/nemotron-4-340b-instruct",
    "nvidia/mistral-nemo-minitron-8b-8k-instruct",
    "nvidia/llama-3.1-nemotron-51b-instruct",
    "nvidia/llama-3.1-nemotron-ultra-253b-v1",
    "nv-mistralai/mistral-nemo-12b-instruct",
]

print("=== EMBEDDING probe ===")
for m in EMBED_CANDIDATES:
    try:
        emb = NVIDIAEmbeddings(model=m)
        vec = emb.embed_query("test")
        print(f"OK   {m}  (dim={len(vec)})")
    except Exception as e:
        print(f"FAIL {m}  -> {str(e)[:120]}")

print("\n=== CHAT probe ===")
for m in CHAT_CANDIDATES:
    try:
        llm = ChatNVIDIA(model=m, temperature=0)
        resp = llm.invoke("Say OK")
        print(f"OK   {m}  -> {resp.content[:40]!r}")
    except Exception as e:
        print(f"FAIL {m}  -> {str(e)[:120]}")
