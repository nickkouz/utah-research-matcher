from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "01_normalizer.md"
VAGUE_TERMS = {"ai stuff", "research", "science", "technology", "computers"}


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _clean_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        parts = [part.strip() for part in value.split(",")]
        return [part for part in parts if part]
    return [str(value).strip()]


def _normalize_text(value: Any) -> str:
    text = str(value or "").strip()
    return text if text else "not specified"


def _clean_interest_phrase(value: str) -> str:
    text = value.strip().rstrip(".")
    prefixes = [
        "i want to use ",
        "i want to work on ",
        "i am interested in ",
        "i'm interested in ",
        "interested in ",
    ]
    lowered = text.lower()
    for prefix in prefixes:
        if lowered.startswith(prefix):
            return text[len(prefix):].strip()
    return text


def _confidence(interests: str) -> str:
    words = interests.split()
    lowered = interests.lower()
    if interests == "not specified" or len(words) < 10 or lowered in VAGUE_TERMS:
        return "low"
    if len(words) < 20:
        return "medium"
    return "high"


def _build_summary(profile: dict[str, Any]) -> str:
    major = _normalize_text(profile.get("major"))
    interests = _clean_interest_phrase(_normalize_text(profile.get("interests_freetext")))
    goal = _normalize_text(profile.get("goal"))
    checkbox_areas = _clean_list(profile.get("checkbox_areas"))
    skills = _clean_list(profile.get("skills"))

    first = f"Undergraduate in {major} seeking research experience in {interests}."

    details = []
    if checkbox_areas:
        details.append("preferred areas include " + ", ".join(checkbox_areas))
    if skills:
        details.append("current technical background includes " + ", ".join(skills))
    if goal != "not specified":
        details.append("career goal: " + goal)

    second = " ".join(details).strip()
    if second:
        return f"{first} {second}."
    return first


def normalize_student_profile(raw_student: dict[str, Any]) -> dict[str, Any]:
    interests = _normalize_text(raw_student.get("interests_freetext"))
    structured_facts = {
        "name": _normalize_text(raw_student.get("name")),
        "major": _normalize_text(raw_student.get("major")),
        "year": _normalize_text(raw_student.get("year")),
        "courses": _clean_list(raw_student.get("courses")),
        "skills": _clean_list(raw_student.get("skills")),
        "time_commitment_hours": int(raw_student.get("commitment_hours") or 0),
        "checkbox_areas": _clean_list(raw_student.get("checkbox_areas")),
    }
    return {
        "structured_facts": structured_facts,
        "research_summary": _build_summary(raw_student),
        "confidence": _confidence(interests),
    }


def load_student(path: str | os.PathLike[str]) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
