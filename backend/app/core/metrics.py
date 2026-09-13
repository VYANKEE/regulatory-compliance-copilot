"""
Prometheus metrics -- business-level counters/histograms, not just generic
HTTP request counts (FastAPI middleware could give us that for free, but
"how many analyses ran" and "how often does the output guardrail reject
something" are the numbers that actually matter for THIS system and need
explicit instrumentation at the point they happen).

Important concept: a Counter only ever goes up (resets on process
restart) -- good for "how many times has X happened total", from which
Prometheus/Grafana derive rates (`rate(x[5m])`) themselves; never
decrement one to represent a current count, that's what Gauge is for. A
Histogram buckets observed values (durations, counts) so you can compute
percentiles (p50/p95/p99) later -- a plain average would hide a slow
tail."""

from prometheus_client import Counter, Histogram

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests handled",
    ["method", "path", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)

analyses_started_total = Counter(
    "analyses_started_total",
    "Total analysis runs enqueued",
)

analyses_completed_total = Counter(
    "analyses_completed_total",
    "Total analysis runs that reached the human_approval pause successfully",
)

analyses_failed_total = Counter(
    "analyses_failed_total",
    "Total analysis runs that raised an exception before reaching approval",
)

approval_decisions_total = Counter(
    "approval_decisions_total",
    "Total HITL approval decisions",
    ["decision"],  # "approved" | "rejected"
)

verified_findings_per_analysis = Histogram(
    "verified_findings_per_analysis",
    "Number of verified findings per completed analysis",
    buckets=(0, 1, 2, 3, 5, 8, 13, 21),
)

guardrail_violations_total = Counter(
    "guardrail_violations_total",
    "Total guardrail violations (input or output)",
    ["layer", "code"],  # layer: "input" | "output"
)
