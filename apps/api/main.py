from __future__ import annotations

import os
import subprocess
import sys

import uvicorn


def run_migrations() -> None:
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)


def main() -> None:
    try:
        run_migrations()
    except subprocess.CalledProcessError as exc:
        print(
            "Startup failed while running Alembic migrations.",
            file=sys.stderr,
        )
        print(
            "Check that DATABASE_URL points to a live Postgres instance and, for production, "
            "that the database supports the pgvector 'vector' extension.",
            file=sys.stderr,
        )
        print(
            "If you are using Railway's default DATABASE_URL, the app now accepts both "
            "'postgresql://' and 'postgresql+psycopg://', but the database itself still needs "
            "pgvector installed for the first migration to succeed.",
            file=sys.stderr,
        )
        raise SystemExit(exc.returncode) from exc
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
