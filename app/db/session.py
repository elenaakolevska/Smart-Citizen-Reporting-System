from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache(maxsize=1)
def _engine() -> Engine:
    """Lazily build the SQLAlchemy engine.

    Building it at import time aborts the whole app if DATABASE_URL is malformed,
    so /health and even the import graph go down with it. Deferring lets the
    server boot and surface the parse error as a clean 500 on the first DB hit.

    Connection args are tuned for Supabase's transaction-mode pooler (port 6543):
      - prepare_threshold=None disables psycopg's prepared-statement cache, which
        PgBouncer in transaction mode cannot maintain across pooled backends and
        would otherwise raise DuplicatePreparedStatement after a handful of calls.
      - pool_recycle keeps us under PgBouncer's idle-disconnect window.
    These settings are no-ops on a direct (5432) connection, so we apply them
    unconditionally rather than sniffing the URL.
    """
    return create_engine(
        get_settings().database_url,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={"prepare_threshold": None},
    )


@lru_cache(maxsize=1)
def _session_factory() -> sessionmaker[Session]:
    return sessionmaker(
        bind=_engine(),
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )


def SessionLocal() -> Session:  # noqa: N802 — keep callable name for back-compat
    return _session_factory()()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a SQLAlchemy session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

