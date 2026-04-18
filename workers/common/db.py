from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Generator

from workers.common.bootstrap import ensure_api_path


ensure_api_path()

from app.db.session import SessionLocal  # noqa: E402


@contextmanager
def worker_session() -> Generator:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

