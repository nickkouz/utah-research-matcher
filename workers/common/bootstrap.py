from __future__ import annotations

import site
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
API_DIR = ROOT_DIR / "apps" / "api"


def ensure_api_path() -> None:
    user_site = site.getusersitepackages()
    if user_site:
        site.addsitedir(user_site)
    if str(API_DIR) not in sys.path:
        sys.path.insert(0, str(API_DIR))


ensure_api_path()
