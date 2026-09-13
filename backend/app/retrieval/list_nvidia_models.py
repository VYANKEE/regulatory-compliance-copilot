"""One-off helper: NVIDIA API se live model list nikaalta hai (kyunki models
baar baar deprecate ho rahe hain, hardcoded naam bharosemand nahi hai)."""

import os

import requests
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("NVIDIA_API_KEY")
if not key:
    raise SystemExit("NVIDIA_API_KEY .env me nahi mili.")

resp = requests.get(
    "https://integrate.api.nvidia.com/v1/models",
    headers={"Authorization": f"Bearer {key}"},
    timeout=30,
)
resp.raise_for_status()
data = resp.json()["data"]

print("=== EMBEDDING models ===")
for m in data:
    mid = m["id"]
    if "embed" in mid.lower():
        print(mid)

print("\n=== CHAT/INSTRUCT models (sample, llama/mistral/qwen) ===")
for m in data:
    mid = m["id"].lower()
    if any(k in mid for k in ["llama", "mistral", "qwen", "instruct"]):
        print(m["id"])
