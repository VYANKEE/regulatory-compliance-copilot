"""
Phase 7: MCP Server.

Important concept: MCP (Model Context Protocol) ka fayda ye hai ki hamara
retrieval + diff logic ek STANDALONE process me expose hota hai — koi bhi MCP
client (Claude Desktop, ya khud hamara Supervisor agent bhi future me) isse
tool ke roop me consume kar sakta hai, bina hamare Python internals import
kiye. Ye credential/process isolation deta hai (agar ye server compromise ho,
blast radius sirf isi process tak — main app ka DB/secrets touch nahi hote)
aur reusability (kal koi Slack bot bhi yahi retrieval tool use kar sakta hai,
bina code duplicate kiye).

Run/test: `mcp dev retrieval_server.py` (MCP inspector UI khulega) ya isse
Claude Desktop config me add karke.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "app" / "retrieval"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "app" / "agents"))

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer

load_dotenv()

mcp = MCPServer("compliance-retrieval")

_store = None


def _get_store():
    global _store
    if _store is None:
        from vectorstore import load_vectorstore

        _store = load_vectorstore()
    return _store


@mcp.tool()
def search_circulars(query: str, k: int = 5) -> list[dict]:
    """RBI circular corpus me semantic search karta hai. Har result me
    chunk_id (citation ke liye), circular_ref, status (current/repealed),
    aur clause text hota hai."""
    docs = _get_store().similarity_search(query, k=k)
    return [
        {
            "chunk_id": d.metadata["chunk_id"],
            "circular_ref": d.metadata["circular_ref"],
            "status": d.metadata["status"],
            "text": d.page_content,
        }
        for d in docs
    ]


@mcp.tool()
def diff_topic(topic: str) -> dict:
    """Ek regulatory topic ke liye purane (repealed) vs naye (current)
    circular clauses ka diff analysis deta hai, citations ke saath."""
    from diff_agent import DiffAgent
    from retrieval_agent import RetrievalAgent

    retrieval = RetrievalAgent()
    diff_agent = DiffAgent()
    ctx = retrieval.get_context(topic)
    result = diff_agent.diff(topic, ctx["current"], ctx["repealed"])
    return result


if __name__ == "__main__":
    mcp.run()
