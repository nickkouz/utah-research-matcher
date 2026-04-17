from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pipeline.openai_client import generate_json


PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "03_rationale.md"


def _clean_bio_phrase(bio: str) -> str:
    text = bio.strip().rstrip(".")
    lowered = text.lower()
    prefixes = (
        "research interests in ",
        "research interests include ",
        "research focuses on ",
        "research focus includes ",
    )
    for prefix in prefixes:
        if lowered.startswith(prefix):
            return text[len(prefix) :].strip()
    return text


def generate_rationale(student_profile: dict[str, Any], match: dict[str, Any]) -> dict[str, str]:
    prompt_result = _generate_rationale_with_model(student_profile, match)
    if prompt_result:
        return prompt_result

    faculty = match["faculty"]
    overlap_terms = match.get("overlap_terms") or []
    overlap_text = ", ".join(overlap_terms[:4]) if overlap_terms else "closely related research interests"
    student_interest = student_profile.get("research_summary", "").split(".", 1)[0]
    strength_label = {
        "strong": "a strong fit",
        "good": "a good fit",
        "possible": "a plausible fit",
    }.get(match.get("match_strength"), "a relevant fit")
    rationale = (
        f"{faculty['name']} is {strength_label} because their work in {_clean_bio_phrase(faculty['bio']).lower()} "
        f"aligns with the student's interests described in '{student_interest}'. "
        f"The strongest areas of overlap are {overlap_text}."
    )
    return {"faculty_id": faculty["id"], "rationale": rationale}


def _generate_rationale_with_model(student_profile: dict[str, Any], match: dict[str, Any]) -> dict[str, str] | None:
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    payload = generate_json(
        system_prompt="You produce concise JSON only.",
        user_prompt=(
            f"{prompt}\n\n"
            f"Student profile JSON:\n{json.dumps(student_profile, indent=2)}\n\n"
            f"Ranked match JSON:\n{json.dumps(match, indent=2)}"
        ),
    )
    if not payload:
        return None

    faculty_id = str(payload.get("faculty_id") or match["faculty"]["id"])
    rationale = str(payload.get("rationale") or "").strip()
    if not rationale:
        return None
    return {"faculty_id": faculty_id, "rationale": rationale}


def apply_rationale_payloads(matches: list[dict[str, Any]], rationale_payloads: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_faculty_id = {payload["faculty_id"]: payload["rationale"] for payload in rationale_payloads}
    for match in matches:
        match["rationale"] = by_faculty_id[match["faculty"]["id"]]
    return matches
