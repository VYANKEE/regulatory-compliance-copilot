"""
DB engine + session factory.

The engine is built at module-load time, but SQLAlchemy's lazy connection
pooling means no connection opens until a real query runs -- so the app
still boots if Postgres is down; a connection error surfaces only at
request time, where FastAPI's exception handler turns it into a clean error.
"""

from ..core.config import get_settings
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

settings = get_settings()

_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.sqlalchemy_database_url, connect_args=_connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency -- yields a session for the request, closing it on
    completion or exception.

    Explicitly commits (harmless even for read-only requests) rather than
    relying on close() alone: close() only rolls back once the connection is
    returned to the pool, which left a brief "idle in transaction" window --
    small, but enough to indefinitely block CREATE INDEX CONCURRENTLY
    (the checkpointer's one-time saver.setup()) given how often the
    dashboard polls."""
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
