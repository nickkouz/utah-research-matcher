from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pipeline.critic import apply_reviews, review_match
from pipeline.emailer import apply_email_payloads, generate_email_modes
from pipeline.normalizer import load_student, normalize_student_profile
from pipeline.openai_client import embed_text, has_openai_client
from pipeline.ranker import load_faculty_db, top_matches
from pipeline.rationale import apply_rationale_payloads, generate_rationale
from pipeline.vagueness import evaluate_vagueness


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RESULTS_PATH = DATA_DIR / "demo_results.json"
PRIMARY_FACULTY_DB_PATH = DATA_DIR / "faculty_db.json"
FALLBACK_FACULTY_DB_PATH = DATA_DIR / "fallback_db.json"


def run_pipeline(student_path: Path | None = None, faculty_path: Path | None = None) -> dict[str, Any]:
    student_raw = load_student(student_path or DATA_DIR / "demo_student.json")
    return run_pipeline_for_student(student_raw, faculty_path=faculty_path)


def run_pipeline_for_student(
    student_raw: dict[str, Any],
    faculty_path: Path | None = None,
) -> dict[str, Any]:
    resolved_faculty_path = faculty_path or resolve_faculty_dataset_path()
    faculty_records = load_faculty_db(resolved_faculty_path)

    student_profile = normalize_student_profile(student_raw)
    _ = evaluate_vagueness(student_profile)
    student_embedding = embed_text(student_profile["research_summary"]) if has_openai_client() else []

    matches = top_matches(student_profile, faculty_records, limit=5, student_embedding=student_embedding)

    rationale_payloads = [generate_rationale(student_profile, match) for match in matches]
    matches = apply_rationale_payloads(matches, rationale_payloads)

    email_payloads = [generate_email_modes(student_profile, match) for match in matches]
    matches = apply_email_payloads(matches, email_payloads)

    reviews = [review_match(student_profile, match) for match in matches]
    matches = apply_reviews(matches, reviews)

    final_matches = [_finalize_match(match) for match in matches]
    result = {"student": student_profile, "matches": final_matches}
    RESULTS_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def resolve_faculty_dataset_path() -> Path:
    if PRIMARY_FACULTY_DB_PATH.exists():
        return PRIMARY_FACULTY_DB_PATH
    return FALLBACK_FACULTY_DB_PATH


def _finalize_match(match: dict[str, Any]) -> dict[str, Any]:
    return {
        "faculty": match["faculty"],
        "score": match["score"],
        "match_strength": match["match_strength"],
        "warning": match["warning"],
        "rationale": match["rationale"],
        "emails": match["emails"],
    }


if __name__ == "__main__":
    print(json.dumps(run_pipeline(), indent=2))
