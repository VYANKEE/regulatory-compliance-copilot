"""Health check -- no auth, no DB, no external calls. Load balancers /
uptime checks hit this."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}
