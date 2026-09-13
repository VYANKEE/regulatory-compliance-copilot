"""
Request correlation ID middleware -- reuses an incoming X-Request-ID header
if present, else generates a UUID, and echoes it back on the response so
client error reports and backend logs can be tied together by that id.
"""

import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from .log_setup import get_logger, request_id_var
from .metrics import http_request_duration_seconds, http_requests_total

logger = get_logger("app.request")


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        token = request_id_var.set(request_id)

        start = time.monotonic()
        try:
            response = await call_next(request)
            duration_seconds = time.monotonic() - start
            response.headers["X-Request-ID"] = request_id

            # route.path (e.g. "/analysis/{thread_id}"), not the raw URL --
            # avoids a Prometheus label per distinct thread_id. Falls back to
            # the raw path on a 404 (no route matched).
            route = request.scope.get("route")
            path_label = route.path if route else request.url.path

            http_requests_total.labels(request.method, path_label, response.status_code).inc()
            http_request_duration_seconds.labels(request.method, path_label).observe(duration_seconds)

            # Must log before reset() -- otherwise request_id_var is already
            # back to "-" for this exact line (verified via TestClient).
            logger.info(
                "request_handled",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_seconds * 1000, 2),
                },
            )
            return response
        finally:
            request_id_var.reset(token)
