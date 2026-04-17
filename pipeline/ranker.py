from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any


TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z\-]+")


def _tokenize(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(text)}


def load_faculty_db(path: str | Path) -> list[dict[str, Any]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _score(student_summary: str, faculty: dict[str, Any]) -> tuple[float, list[str]]:
    student_tokens = _tokenize(student_summary)
    faculty_tokens = _tokenize(faculty.get("research_text", ""))
    overlap = sorted(student_tokens & faculty_tokens)
    union = student_tokens | faculty_tokens
    jaccard = len(overlap) / len(union) if union else 0.0

    recent_year = int(faculty.get("last_active_year") or 0)
    recency_bonus = 0.05 if recent_year >= 2024 else 0.0
    score = jaccard + recency_bonus
    return score, overlap[:8]


def top_matches(student_profile: dict[str, Any], faculty_records: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    student_summary = student_profile.get("research_summary", "")
    matches = []
    for faculty in faculty_records:
        score, overlap = _score(student_summary, faculty)
        matches.append(
            {
                "faculty": faculty,
                "score": round(score, 4),
                "overlap_terms": overlap,
                "match_strength": _match_strength(score),
                "warning": None if int(faculty.get("last_active_year") or 0) >= 2023 else "Research activity may be dated.",
            }
        )
    matches.sort(key=lambda item: item["score"], reverse=True)
    return matches[:limit]


def _match_strength(score: float) -> str:
    if score >= 0.18:
        return "strong"
    if score >= 0.1:
        return "good"
    return "possible"
