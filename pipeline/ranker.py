from __future__ import annotations

import json
import math
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from pipeline.faculty_data import load_faculty_db
from pipeline.openai_client import embed_text, generate_structured_json, has_openai_client


PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "06_reranker.md"
TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z\-]+")
SUMMARY_WEIGHT = 0.55
FACET_WEIGHT = 0.20
KEYWORD_WEIGHT = 0.15
RECENCY_WEIGHT = 0.05
UNDERGRAD_WEIGHT = 0.05
RERANK_LIMIT = 20
DIVERSITY_LAMBDA = 0.12
CURRENT_YEAR = datetime.now().year


def top_matches(
    student_profile: dict[str, Any],
    faculty_records: list[dict[str, Any]],
    limit: int = 5,
    student_embedding: list[float] | None = None,
) -> list[dict[str, Any]]:
    eligible = [faculty for faculty in faculty_records if faculty.get("eligible_for_matching")]
    if not eligible:
        eligible = list(faculty_records)

    student_summary = student_profile.get("research_summary", "")
    student_facets_text = _student_facets_text(student_profile)
    summary_embedding = student_embedding if student_embedding is not None else embed_text(student_summary)
    facet_embedding = embed_text(student_facets_text)

    candidates = [
        _score_candidate(student_profile, summary_embedding or [], facet_embedding or [], faculty)
        for faculty in eligible
    ]
    candidates.sort(key=lambda item: (-item["score"], item["faculty"]["name"]))

    reranked = _rerank_candidates(student_profile, candidates[:RERANK_LIMIT])
    diversified = _apply_diversity(reranked, limit=limit)
    diversified.sort(key=lambda item: (-item["score"], item["faculty"]["name"]))
    return diversified[:limit]


def _score_candidate(
    student_profile: dict[str, Any],
    summary_embedding: list[float],
    facet_embedding: list[float],
    faculty: dict[str, Any],
) -> dict[str, Any]:
    student_summary = student_profile.get("research_summary", "")
    faculty_summary = faculty.get("normalized_research_summary", "")
    faculty_papers = faculty.get("paper_titles_text", "")

    summary_similarity = _embedding_or_lexical_similarity(
        summary_embedding,
        faculty.get("embedding_summary", []),
        student_summary,
        faculty_summary,
    )
    facet_similarity = _embedding_or_lexical_similarity(
        facet_embedding,
        faculty.get("embedding_papers", []),
        _student_facets_text(student_profile),
        faculty_papers or faculty.get("research_text", ""),
    )
    keyword_overlap_score, overlap_terms = _keyword_overlap(student_profile, faculty)
    recency_score = _recency_score(faculty.get("last_active_year", 0))
    undergrad_score = _undergrad_score(faculty.get("accepts_undergrads"))

    base_score = (
        (summary_similarity * SUMMARY_WEIGHT)
        + (facet_similarity * FACET_WEIGHT)
        + (keyword_overlap_score * KEYWORD_WEIGHT)
        + (recency_score * RECENCY_WEIGHT)
        + (undergrad_score * UNDERGRAD_WEIGHT)
    )

    candidate = {
        "faculty": faculty,
        "score": round(base_score, 4),
        "base_score": round(base_score, 4),
        "overlap_terms": overlap_terms,
        "component_scores": {
            "summary_similarity": round(summary_similarity, 4),
            "facet_similarity": round(facet_similarity, 4),
            "keyword_overlap": round(keyword_overlap_score, 4),
            "recency": round(recency_score, 4),
            "undergrad_friendliness": round(undergrad_score, 4),
        },
        "match_strength": _match_strength(base_score),
        "warning": _warning_for_faculty(faculty),
        "rerank_notes": "",
    }
    return candidate


def _student_facets_text(student_profile: dict[str, Any]) -> str:
    methods = ", ".join(student_profile.get("research_methods", []))
    domains = ", ".join(student_profile.get("application_domains", []))
    keywords = ", ".join(student_profile.get("interest_keywords", []))
    experience = ", ".join(student_profile.get("experience_signals", []))
    return (
        f"Methods: {methods}. "
        f"Application domains: {domains}. "
        f"Interest keywords: {keywords}. "
        f"Experience signals: {experience}."
    )


def _embedding_or_lexical_similarity(
    left_embedding: list[float],
    right_embedding: list[float],
    left_text: str,
    right_text: str,
) -> float:
    embedding_score = _cosine_similarity(left_embedding, right_embedding)
    if embedding_score > 0:
        return embedding_score
    return _jaccard_similarity(left_text, right_text)


def _keyword_overlap(
    student_profile: dict[str, Any],
    faculty: dict[str, Any],
) -> tuple[float, list[str]]:
    student_keywords = _normalize_keyword_set(
        list(student_profile.get("research_methods", []))
        + list(student_profile.get("application_domains", []))
        + list(student_profile.get("interest_keywords", []))
        + list(student_profile.get("structured_facts", {}).get("skills", []))
    )
    faculty_keywords = _normalize_keyword_set(faculty.get("research_keywords", []))
    overlap = sorted(student_keywords & faculty_keywords)
    union = student_keywords | faculty_keywords
    score = len(overlap) / len(union) if union else 0.0
    return score, overlap[:8]


def _normalize_keyword_set(values: list[str]) -> set[str]:
    normalized = set()
    for value in values:
        text = str(value).strip().lower()
        if text:
            normalized.add(text)
    return normalized


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(l * r for l, r in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return max(dot / (left_norm * right_norm), 0.0)


def _jaccard_similarity(left_text: str, right_text: str) -> float:
    left_tokens = {token.lower() for token in TOKEN_RE.findall(left_text)}
    right_tokens = {token.lower() for token in TOKEN_RE.findall(right_text)}
    if not left_tokens or not right_tokens:
        return 0.0
    overlap = left_tokens & right_tokens
    union = left_tokens | right_tokens
    return len(overlap) / len(union)


def _recency_score(last_active_year: int) -> float:
    if not last_active_year:
        return 0.2
    delta = CURRENT_YEAR - last_active_year
    if delta <= 1:
        return 1.0
    if delta == 2:
        return 0.8
    if delta == 3:
        return 0.5
    return 0.2


def _undergrad_score(accepts_undergrads: bool | None) -> float:
    if accepts_undergrads is True:
        return 1.0
    if accepts_undergrads is False:
        return 0.1
    return 0.5


def _match_strength(score: float) -> str:
    if score >= 0.24:
        return "strong"
    if score >= 0.16:
        return "good"
    return "possible"


def _warning_for_faculty(faculty: dict[str, Any]) -> str | None:
    year = faculty.get("last_active_year", 0)
    if year and year < CURRENT_YEAR - 3:
        return "Recent publication activity may be limited."
    if faculty.get("accepts_undergrads") is False:
        return "This faculty member may not currently take undergraduates."
    if not faculty.get("eligible_for_matching"):
        return "This faculty record has limited research signal."
    return None


def _rerank_candidates(
    student_profile: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not candidates:
        return []

    reranked = _rerank_with_model(student_profile, candidates)
    if reranked:
        return reranked
    return candidates


def _rerank_with_model(
    student_profile: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]] | None:
    if not has_openai_client():
        return None

    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["ranked_faculty"],
        "properties": {
            "ranked_faculty": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["faculty_id", "rubric_score", "notes"],
                    "properties": {
                        "faculty_id": {"type": "string"},
                        "rubric_score": {"type": "number"},
                        "notes": {"type": "string"},
                    },
                },
            }
        },
    }
    payload = generate_structured_json(
        system_prompt=(
            "You rerank faculty matches for precision. "
            "Ground every ranking decision in the student profile and candidate faculty data only."
        ),
        user_prompt=(
            f"{prompt}\n\n"
            f"Student profile JSON:\n{json.dumps(student_profile, indent=2)}\n\n"
            f"Candidate matches JSON:\n{json.dumps(candidates, indent=2)}"
        ),
        schema_name="faculty_rerank",
        json_schema=schema,
    )
    if not payload:
        return None

    ranked_faculty = payload.get("ranked_faculty")
    if not isinstance(ranked_faculty, list):
        return None

    by_id = {candidate["faculty"]["id"]: dict(candidate) for candidate in candidates}
    reranked = []
    seen = set()
    for item in ranked_faculty:
        if not isinstance(item, dict):
            continue
        faculty_id = str(item.get("faculty_id") or "").strip()
        if faculty_id not in by_id or faculty_id in seen:
            continue
        candidate = by_id[faculty_id]
        rubric_score = float(item.get("rubric_score") or 0)
        candidate["score"] = round((candidate["base_score"] * 0.6) + (rubric_score * 0.4), 4)
        candidate["match_strength"] = _match_strength(candidate["score"])
        candidate["rerank_notes"] = str(item.get("notes") or "").strip()
        reranked.append(candidate)
        seen.add(faculty_id)

    for candidate in candidates:
        faculty_id = candidate["faculty"]["id"]
        if faculty_id not in seen:
            reranked.append(candidate)
    reranked.sort(key=lambda item: (-item["score"], item["faculty"]["name"]))
    return reranked


def _apply_diversity(candidates: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if len(candidates) <= 1:
        return candidates[:limit]

    remaining = list(candidates)
    selected = []
    while remaining and len(selected) < limit:
        if not selected:
            chosen = remaining.pop(0)
            selected.append(chosen)
            continue

        best_index = 0
        best_value = None
        for index, candidate in enumerate(remaining):
            similarity_penalty = max(
                _faculty_similarity(candidate["faculty"], chosen["faculty"])
                for chosen in selected
            )
            mmr_value = candidate["score"] - (DIVERSITY_LAMBDA * similarity_penalty)
            if best_value is None or mmr_value > best_value:
                best_value = mmr_value
                best_index = index

        selected.append(remaining.pop(best_index))
    return selected


def _faculty_similarity(left: dict[str, Any], right: dict[str, Any]) -> float:
    left_keywords = set(keyword.lower() for keyword in left.get("research_keywords", []))
    right_keywords = set(keyword.lower() for keyword in right.get("research_keywords", []))
    keyword_similarity = 0.0
    if left_keywords or right_keywords:
        union = left_keywords | right_keywords
        keyword_similarity = len(left_keywords & right_keywords) / len(union) if union else 0.0

    same_department = 1.0 if left.get("department") == right.get("department") else 0.0
    return (keyword_similarity * 0.8) + (same_department * 0.2)
