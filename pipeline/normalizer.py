from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any


PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "01_normalizer.md"
VAGUE_TERMS = {
    "ai stuff",
    "research",
    "science",
    "technology",
    "computers",
    "anything",
    "not sure",
}
INTEREST_PREFIXES = (
    "i want to use ",
    "i want to work on ",
    "i am interested in ",
    "i'm interested in ",
    "interested in ",
    "i like ",
)


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def load_student(path: str | os.PathLike[str]) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _clean_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        items = value.split(",")
    else:
        items = [value]
    cleaned = []
    for item in items:
        text = str(item).strip()
        if text and text not in cleaned:
            cleaned.append(text)
    return cleaned


def _normalize_text(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text if text else "not specified"


def _clean_interest_phrase(value: str) -> str:
    if value == "not specified":
        return value
    text = value.strip().rstrip(".")
    lowered = text.lower()
    for prefix in INTEREST_PREFIXES:
        if lowered.startswith(prefix):
            return text[len(prefix) :].strip()
    return text


def _normalize_research_phrase(value: str) -> str:
    phrase = _clean_interest_phrase(_normalize_text(value))
    if phrase == "not specified":
        return phrase
    phrase = phrase.rstrip(".")
    replacements = {
        "ai": "artificial intelligence",
        "ai/ml": "artificial intelligence and machine learning",
        "ml": "machine learning",
        "nlp": "natural language processing",
    }
    words = phrase.split()
    normalized_words = [replacements.get(word.lower(), word) for word in words]
    return " ".join(normalized_words)


def _confidence(interests: str) -> str:
    lowered = interests.lower()
    words = lowered.split()
    if interests == "not specified" or lowered in VAGUE_TERMS or len(words) < 10:
        return "low"
    if len(words) < 20:
        return "medium"
    return "high"


def _build_summary(profile: dict[str, Any]) -> str:
    major = _normalize_text(profile.get("major"))
    interests = _normalize_research_phrase(profile.get("interests_freetext"))
    skills = _clean_list(profile.get("skills"))
    checkbox_areas = _clean_list(profile.get("checkbox_areas"))
    goal = _normalize_text(profile.get("goal"))

    first_sentence = f"Undergraduate in {major} seeking research experience in {interests}."

    detail_parts = []
    if checkbox_areas:
        detail_parts.append("Preferred areas include " + ", ".join(checkbox_areas))
    if skills:
        detail_parts.append("Current technical background includes " + ", ".join(skills))
    if goal != "not specified":
        detail_parts.append("Career goal: " + goal)

    if detail_parts:
        return first_sentence + " " + ". ".join(detail_parts) + "."
    return first_sentence


def normalize_student_profile(raw_student: dict[str, Any]) -> dict[str, Any]:
    normalized_interests = _normalize_research_phrase(raw_student.get("interests_freetext"))
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
        "confidence": _confidence(normalized_interests),
    }
