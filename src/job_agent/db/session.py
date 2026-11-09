"""Engine and session factory bootstrap."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from job_agent.config import get_settings
from job_agent.db.base import Base
from job_agent.logging_setup import get_logger

# Import models so metadata registers all tables before create_all.
from job_agent.models import application as _application  # noqa: F401
from job_agent.models import job as _job  # noqa: F401

pclog = get_logger(__name__)

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Create or return the process-wide SQLAlchemy engine.

    Returns:
        Shared ``Engine`` pointed at ``DATABASE_URL``.
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args = {}
        if settings.database_url.startswith("sqlite"):
            # SQLite needs check_same_thread=False for FastAPI request threads.
            connect_args["check_same_thread"] = False
        _engine = create_engine(settings.database_url, connect_args=connect_args)

        @event.listens_for(_engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:  # noqa: ARG001
            if settings.database_url.startswith("sqlite"):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        pclog.info("Created DB engine for url_scheme=%s", settings.database_url.split(":")[0])
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Return a cached sessionmaker bound to the shared engine.

    Returns:
        ``sessionmaker`` producing ``Session`` instances.
    """
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _session_factory


def init_db() -> None:
    """Create all tables if they do not already exist."""
    engine = get_engine()
    # Create schema from registered declarative models.
    Base.metadata.create_all(bind=engine)
    pclog.info("Initialized database schema tables=%s", list(Base.metadata.tables))


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a transactional scope around a series of operations.

    Yields:
        An open SQLAlchemy ``Session``.

    Raises:
        Exception: Re-raises after rollback on any failure inside the block.
    """
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        pclog.error("DB session rolled back due to error", exc_info=True)
        raise
    finally:
        session.close()
