from __future__ import annotations

import re
import unicodedata


NON_WORD_RE = re.compile(r"[^a-z0-9]+")


def normalize_whitespace(value: str | None) -> str:
    return " ".join((value or "").split()).strip()


def normalize_name(value: str | None) -> str:
    text = normalize_whitespace(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return text


def slugify(value: str | None) -> str:
    text = normalize_name(value).lower()
    return NON_WORD_RE.sub("_", text).strip("_")

