from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from pipeline.openai_client import embed_text


TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z\-]+")
EMBEDDING_MATCH_WEIGHT = 0.8
LEXICAL_MATCH_WEIGHT = 0.2


def load_faculty_db(path: str | Path) -> list[dict[str, Any]]:
    records = json.loads(Path(path).read_text(encoding="utf-8"))
    return [_normalize_faculty_record(record) for record in records]


def _normalize_faculty_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(record.get("id") or "not_specified"),
        "name": str(record.get("name") or "not specified"),
        "title": str(record.get("title") or "not specified"),
        "department": str(record.get("department") or "not specified"),
        "email": str(record.get("email") or "not specified"),
        "profile_url": str(record.get("profile_url") or ""),
        "bio": str(record.get("bio") or "not specified"),
        "recent_papers": record.get("recent_papers") or [],
        "research_text": str(record.get("research_text") or record.get("bio") or ""),
        "embedding": record.get("embedding") or [],
        "last_active_year": int(record.get("last_active_year") or 0),
        "accepts_undergrads": record.get("accepts_undergrads"),
    }


def _tokenize(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(text)}


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(l * r for l, r in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def _lexical_score(student_summary: str, faculty_text: str) -> tuple[float, list[str]]:
    student_tokens = _tokenize(student_summary)
    faculty_tokens = _tokenize(faculty_text)
    overlap = sorted(student_tokens & faculty_tokens)
    union = student_tokens | faculty_tokens
    jaccard = len(overlap) / len(union) if union else 0.0
    return jaccard, overlap[:8]


def _score_match(
    student_profile: dict[str, Any],
    student_embedding: list[float],
    faculty: dict[str, Any],
) -> dict[str, Any]:
    lexical_score, overlap = _lexical_score(
        student_profile.get("research_summary", ""),
        faculty.get("research_text", ""),
    )
    embedding_score = _cosine_similarity(student_embedding, faculty.get("embedding", []))
    if embedding_score > 0:
        score = (embedding_score * EMBEDDING_MATCH_WEIGHT) + (lexical_score * LEXICAL_MATCH_WEIGHT)
    else:
        score = lexical_score

    recent_year = faculty.get("last_active_year", 0)
    if recent_year >= 2024:
        score += 0.03
    elif recent_year and recent_year < 2022:
        score -= 0.02

    return {
        "faculty": faculty,
        "score": round(max(score, 0.0), 4),
        "overlap_terms": overlap,
        "match_strength": _match_strength(score),
        "warning": _warning_for_faculty(faculty),
    }


def top_matches(
    student_profile: dict[str, Any],
    faculty_records: list[dict[str, Any]],
    limit: int = 5,
    student_embedding: list[float] | None = None,
) -> list[dict[str, Any]]:
    if student_embedding is None:
        student_embedding = embed_text(student_profile.get("research_summary", ""))

    ranked = [
        _score_match(student_profile, student_embedding or [], faculty)
        for faculty in faculty_records
    ]
    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked[:limit]


def _match_strength(score: float) -> str:
    if score >= 0.25:
        return "strong"
    if score >= 0.12:
        return "good"
    return "possible"


def _warning_for_faculty(faculty: dict[str, Any]) -> str | None:
    year = faculty.get("last_active_year", 0)
    if year and year < 2022:
        return "Recent research activity may be limited."
    if faculty.get("email") == "not specified":
        return "Faculty contact information may be incomplete."
    return None
