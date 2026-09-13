"""
RQ (Redis Queue) setup -- the background job queue analysis runs enqueue to.

/analysis/start only enqueues (milliseconds) instead of running the full
6-topic pipeline inline, avoiding client timeouts and a worker tied up for
the whole run. The actual work happens in jobs/worker.py, which can scale
to multiple parallel processes; the queue itself acts as a natural
backpressure buffer under load.
"""

import redis
from rq import Queue

from ..core.config import get_settings

_queue: "Queue | None" = None


def get_queue() -> Queue:
    global _queue
    if _queue is None:
        settings = get_settings()
        conn = redis.from_url(settings.redis_url)
        _queue = Queue("analysis", connection=conn)
    return _queue
