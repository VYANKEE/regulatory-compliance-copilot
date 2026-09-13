"""
FastAPI entrypoint. Run with: `uvicorn app.main:app --reload` from the
`backend/` directory.

Exception handlers are registered explicitly so any guardrail violation or
internal error returns a clean {reason, code} JSON, never a raw traceback.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "guardrails"))

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .api.routes import analysis, health, policies
from .core.config import get_settings
from .core.log_setup import configure_logging, get_logger
from .core.metrics import guardrail_violations_total
from .core.middleware import RequestIdMiddleware
from .core.tracing import configure_tracing
from .db.base import Base
from .db.session import engine
from .guardrails.input_guardrails import GuardrailViolation
from .guardrails.output_guardrails import OutputGuardrailViolation

settings = get_settings()
configure_logging(level=settings.log_level)
logger = get_logger("app.main")

app = FastAPI(title="Regulatory Compliance Copilot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIdMiddleware)

configure_tracing(app)

app.include_router(health.router)
app.include_router(policies.router)
app.include_router(analysis.router)


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    """Prometheus scrapes this. No auth on purpose -- reached only from
    inside the cluster network in a real deployment, not the public internet."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.on_event("startup")
def on_startup() -> None:
    # Dev convenience: auto-creates tables on sqlite/local Postgres.
    # Production should use Alembic migrations instead (see backend/alembic/).
    Base.metadata.create_all(bind=engine)
    logger.info("startup_complete", extra={"environment": settings.environment})


@app.exception_handler(GuardrailViolation)
async def input_guardrail_handler(request: Request, exc: GuardrailViolation) -> JSONResponse:
    guardrail_violations_total.labels("input", exc.code).inc()
    logger.warning("input_guardrail_violation", extra={"code": exc.code})
    return JSONResponse(status_code=400, content={"error": exc.code, "detail": exc.reason})


@app.exception_handler(OutputGuardrailViolation)
async def output_guardrail_handler(request: Request, exc: OutputGuardrailViolation) -> JSONResponse:
    guardrail_violations_total.labels("output", exc.code).inc()
    logger.warning("output_guardrail_violation", extra={"code": exc.code})
    return JSONResponse(status_code=502, content={"error": exc.code, "detail": exc.reason})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Never a raw traceback to the client -- only to server logs.
    logger.exception("unhandled_exception", extra={"exception_type": type(exc).__name__})
    return JSONResponse(status_code=500, content={"error": "internal_error", "detail": "Something went wrong."})
