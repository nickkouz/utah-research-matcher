from __future__ import annotations

import os
import subprocess
import sys

import uvicorn


def run_migrations() -> None:
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)


def main() -> None:
    run_migrations()
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
