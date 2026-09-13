"""Step-by-step diagnostic: vectorstore.py jaisa hi stack, par har step ke
baad print+flush taaki exactly pata chale kahan atakta/crash hota hai."""

import sys

print("1. starting imports...", flush=True)
from dotenv import load_dotenv
print("2. dotenv imported", flush=True)

load_dotenv()
print("3. .env loaded", flush=True)

from langchain_core.documents import Document
print("4. langchain_core imported", flush=True)

from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
print("5. langchain_nvidia_ai_endpoints imported", flush=True)

emb = NVIDIAEmbeddings(model="nvidia/nemotron-3-embed-1b")
print("6. embeddings object created", flush=True)

from langchain_chroma import Chroma
print("7. langchain_chroma imported", flush=True)

store = Chroma(
    collection_name="diag_test",
    embedding_function=emb,
    persist_directory="diag_chroma_db",
)
print("8. Chroma store created (empty)", flush=True)

doc = Document(page_content="Yeh ek test chunk hai DLG cap ke baare mein.", metadata={"chunk_id": "test::1"})
print("9. about to call add_documents (this is the actual embedding API call)...", flush=True)

store.add_documents([doc])
print("10. add_documents SUCCEEDED", flush=True)

print("ALL STEPS PASSED", flush=True)
