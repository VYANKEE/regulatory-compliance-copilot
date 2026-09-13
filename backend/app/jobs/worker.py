"""
RQ worker entrypoint. Run from `backend/` with venv active:

    python -m app.jobs.worker

Multiple worker processes can run at once (RQ ensures one job goes to only
one worker) for horizontal throughput.

RQ's default Worker forks a child process per job (isolation: one crashed
job doesn't take down the worker), but os.fork() doesn't exist on Windows.
SimpleWorker runs jobs in-process instead, so it's used on Windows; Linux
deployments get the fully-isolated Worker. Chosen automatically by platform.
"""

import sys

import redis
from rq import Worker
from rq.worker import SimpleWorker

from ..core.config import get_settings


def main() -> None:
    settings = get_settings()
    conn = redis.from_url(settings.redis_url)
    worker_cls = SimpleWorker if sys.platform == "win32" else Worker
    worker = worker_cls(["analysis"], connection=conn)
    print(f"RQ worker starting ({worker_cls.__name__}), listening on queue: analysis")
    worker.work()


if __name__ == "__main__":
    main()
