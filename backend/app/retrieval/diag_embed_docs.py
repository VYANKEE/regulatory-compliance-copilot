"""Sirf embed_documents (passage type) test karta hai, Chroma ke bina —
taaki pata chale crash Chroma ki wajah se hai ya seedha NVIDIA embedding
call (passage type) ki wajah se."""

from dotenv import load_dotenv

load_dotenv()

from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

print("1. creating embeddings object...", flush=True)
emb = NVIDIAEmbeddings(model="nvidia/nemotron-3-embed-1b")
print("2. object created, calling embed_documents (passage type)...", flush=True)

result = emb.embed_documents(["Yeh ek test chunk hai DLG cap ke baare mein."])
print(f"3. SUCCESS, got {len(result)} embeddings, dim={len(result[0])}", flush=True)
