from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from pipeline.openai_client import generate_structured_json


PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "01_normalizer.md"
TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z\-]+")
INTEREST_PREFIXES = (
    "i want to use ",
    "i want to work on ",
    "i want to study ",
    "i am interested in ",
    "i'm interested in ",
    "interested in ",
    "i like ",
)
METHOD_VOCAB = {
    "artificial intelligence",
    "computer vision",
    "deep learning",
    "human-computer interaction",
    "machine learning",
    "natural language processing",
    "nlp",
    "robotics",
    "security",
    "systems",
}
APPLICATION_VOCAB = {
    "accessibility",
    "climate",
    "education",
    "finance",
    "healthcare",
    "robotics",
    "scientific computing",
    "social good",
    "sustainability",
}
VAGUE_PHRASES = {
    "ai",
    "ai stuff",
    "anything",
    "computers",
    "research",
    "science",
    "technology",
}
STOPWORDS = {
    "a",
    "about",
    "an",
    "and",
    "applications",
    "area",
    "for",
    "help",
    "i",
    "in",
    "interested",
    "like",
    "maybe",
    "of",
    "on",
    "research",
    "systems",
    "that",
    "the",
    "to",
    "use",
    "using",
    "want",
    "with",
    "work",
}


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def load_student(path: str | os.PathLike[str]) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def normalize_student_profile(raw_student: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_with_model(raw_student)
    if not normalized:
        normalized = _normalize_with_rules(raw_student)

    normalized["needs_followup"] = normalized.get("confidence") == "low"
    normalized["followup_question"] = (
        _followup_question(raw_student, normalized) if normalized["needs_followup"] else ""
    )
    return normalized


def _normalize_with_model(raw_student: dict[str, Any]) -> dict[str, Any] | None:
    primary_interest = _primary_interest_text(raw_student)
    prompt = load_prompt()
    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "structured_facts",
            "research_summary",
            "research_methods",
            "application_domains",
            "interest_keywords",
            "experience_signals",
            "confidence",
        ],
        "properties": {
            "structured_facts": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "name",
                    "email",
                    "major",
                    "year",
                    "courses",
                    "skills",
                    "time_commitment_hours",
                    "checkbox_areas",
                    "application_areas",
                    "methods",
                    "reference_examples",
                ],
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "major": {"type": "string"},
                    "year": {"type": "string"},
                    "courses": {"type": "array", "items": {"type": "string"}},
                    "skills": {"type": "array", "items": {"type": "string"}},
                    "time_commitment_hours": {"type": "integer"},
                    "checkbox_areas": {"type": "array", "items": {"type": "string"}},
                    "application_areas": {"type": "array", "items": {"type": "string"}},
                    "methods": {"type": "array", "items": {"type": "string"}},
                    "reference_examples": {"type": "array", "items": {"type": "string"}},
                },
            },
            "research_summary": {"type": "string"},
            "research_methods": {"type": "array", "items": {"type": "string"}},
            "application_domains": {"type": "array", "items": {"type": "string"}},
            "interest_keywords": {"type": "array", "items": {"type": "string"}},
            "experience_signals": {"type": "array", "items": {"type": "string"}},
            "confidence": {
                "type": "string",
                "enum": ["high", "medium", "low"],
            },
        },
    }

    payload = generate_structured_json(
        system_prompt=(
            "You are a research advisor who converts student form input into precise, honest JSON. "
            "Never invent research interests, methods, or skills."
        ),
        user_prompt=(
            f"{prompt}\n\n"
            "Additional required output fields:\n"
            "- research_methods: methods explicitly stated or directly implied by the student selections only\n"
            "- application_domains: domains explicitly stated by the student selections or text only\n"
            "- interest_keywords: concise keywords grounded in the student's stated interests only\n"
            "- experience_signals: courses, skills, or examples explicitly provided by the student\n\n"
            f"Primary interest text: {primary_interest}\n"
            f"Raw student JSON:\n{json.dumps(raw_student, indent=2)}"
        ),
        schema_name="normalized_student_profile",
        json_schema=schema,
    )
    if not payload:
        return None

    structured = payload.get("structured_facts")
    if not isinstance(structured, dict):
        return None

    return {
        "structured_facts": {
            "name": _normalize_text(structured.get("name")),
            "email": _normalize_text(structured.get("email")),
            "major": _normalize_text(structured.get("major")),
            "year": _normalize_text(structured.get("year")),
            "courses": _clean_list(structured.get("courses")),
            "skills": _clean_list(structured.get("skills")),
            "time_commitment_hours": _to_int(structured.get("time_commitment_hours")),
            "checkbox_areas": _clean_list(structured.get("checkbox_areas")),
            "application_areas": _clean_list(structured.get("application_areas")),
            "methods": _clean_list(structured.get("methods")),
            "reference_examples": _clean_list(structured.get("reference_examples")),
        },
        "research_summary": _normalize_text(payload.get("research_summary")),
        "research_methods": _clean_list(payload.get("research_methods")),
        "application_domains": _clean_list(payload.get("application_domains")),
        "interest_keywords": _clean_list(payload.get("interest_keywords")),
        "experience_signals": _clean_list(payload.get("experience_signals")),
        "confidence": _clean_confidence(payload.get("confidence")),
    }


def _normalize_with_rules(raw_student: dict[str, Any]) -> dict[str, Any]:
    primary_interest = _primary_interest_text(raw_student)
    structured_facts = {
        "name": _normalize_text(raw_student.get("name")),
        "email": _normalize_text(raw_student.get("email")),
        "major": _normalize_text(raw_student.get("major")),
        "year": _normalize_text(raw_student.get("year")),
        "courses": _clean_list(raw_student.get("courses")),
        "skills": _clean_list(raw_student.get("skills")),
        "time_commitment_hours": _to_int(raw_student.get("commitment_hours")),
        "checkbox_areas": _clean_list(raw_student.get("checkbox_areas")),
        "application_areas": _clean_list(raw_student.get("application_areas")),
        "methods": _clean_list(raw_student.get("methods")),
        "reference_examples": _clean_reference_examples(raw_student.get("reference_examples")),
    }

    research_methods = _merge_unique(
        structured_facts["methods"],
        [value for value in structured_facts["checkbox_areas"] if _is_method(value)],
        _extract_vocab_matches(primary_interest, METHOD_VOCAB),
    )
    application_domains = _merge_unique(
        structured_facts["application_areas"],
        [value for value in structured_facts["checkbox_areas"] if _is_application(value)],
        _extract_vocab_matches(primary_interest, APPLICATION_VOCAB),
    )
    interest_keywords = _derive_interest_keywords(
        primary_interest,
        research_methods,
        application_domains,
        structured_facts["reference_examples"],
    )
    experience_signals = _merge_unique(
        structured_facts["courses"][:4],
        structured_facts["skills"][:6],
        structured_facts["reference_examples"][:4],
    )
    confidence = _confidence(primary_interest, research_methods, application_domains, structured_facts["reference_examples"])

    return {
        "structured_facts": structured_facts,
        "research_summary": _build_summary(
            major=structured_facts["major"],
            primary_interest=primary_interest,
            methods=research_methods,
            application_domains=application_domains,
            experience_signals=experience_signals,
            goal=_normalize_text(raw_student.get("goal")),
        ),
        "research_methods": research_methods,
        "application_domains": application_domains,
        "interest_keywords": interest_keywords,
        "experience_signals": experience_signals,
        "confidence": confidence,
    }


def _normalize_text(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text if text else "not specified"


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
    seen = set()
    for item in items:
        text = str(item).strip()
        if text:
            lowered = text.lower()
            if lowered not in seen:
                cleaned.append(text)
                seen.add(lowered)
    return cleaned


def _clean_reference_examples(value: Any) -> list[str]:
    if isinstance(value, list):
        return _clean_list(value)
    text = str(value or "")
    parts = re.split(r"[\n,;]+", text)
    return _clean_list(parts)


def _merge_unique(*groups: list[str]) -> list[str]:
    merged = []
    seen = set()
    for group in groups:
        for item in group:
            text = str(item).strip()
            if not text:
                continue
            lowered = text.lower()
            if lowered not in seen:
                merged.append(text)
                seen.add(lowered)
    return merged


def _primary_interest_text(raw_student: dict[str, Any]) -> str:
    base = _clean_interest_phrase(_normalize_text(
        raw_student.get("primary_interest_text") or raw_student.get("interests_freetext")
    ))
    followup = _normalize_text(raw_student.get("followup_answer"))
    if followup != "not specified":
        return f"{base}. Additional detail: {followup}"
    return base


def _clean_interest_phrase(text: str) -> str:
    if text == "not specified":
        return text
    lowered = text.lower()
    for prefix in INTEREST_PREFIXES:
        if lowered.startswith(prefix):
            return text[len(prefix):].strip().rstrip(".")
    return text.rstrip(".")


def _extract_vocab_matches(text: str, vocabulary: set[str]) -> list[str]:
    lowered = text.lower()
    matches = []
    for item in sorted(vocabulary, key=len, reverse=True):
        if item in lowered:
            matches.append(_title_case_keyword(item))
    return matches


def _title_case_keyword(keyword: str) -> str:
    replacements = {
        "nlp": "Natural Language Processing",
        "human-computer interaction": "Human-Computer Interaction",
        "machine learning": "Machine Learning",
        "natural language processing": "Natural Language Processing",
    }
    if keyword in replacements:
        return replacements[keyword]
    return " ".join(part.capitalize() for part in keyword.split())


def _derive_interest_keywords(
    primary_interest: str,
    methods: list[str],
    application_domains: list[str],
    reference_examples: list[str],
) -> list[str]:
    keywords = _merge_unique(methods, application_domains)
    tokens = []
    for token in TOKEN_RE.findall(primary_interest):
        lowered = token.lower()
        if lowered in STOPWORDS or len(lowered) < 4:
            continue
        if lowered not in tokens:
            tokens.append(lowered)
    keywords.extend(token for token in tokens[:8] if token not in {item.lower() for item in keywords})
    keywords.extend(example for example in reference_examples[:3] if example not in keywords)
    return keywords[:12]


def _build_summary(
    major: str,
    primary_interest: str,
    methods: list[str],
    application_domains: list[str],
    experience_signals: list[str],
    goal: str,
) -> str:
    first_sentence = f"Undergraduate in {major} seeking research experience in {primary_interest.rstrip('.')}."

    detail_parts = []
    if methods:
        detail_parts.append("Methods of interest include " + ", ".join(methods))
    if application_domains:
        detail_parts.append("Application areas include " + ", ".join(application_domains))
    if experience_signals:
        detail_parts.append("Relevant background includes " + ", ".join(experience_signals[:5]))
    if goal != "not specified":
        detail_parts.append("Career goal: " + goal)

    return first_sentence + (" " + ". ".join(detail_parts) + "." if detail_parts else "")


def _confidence(
    primary_interest: str,
    methods: list[str],
    application_domains: list[str],
    reference_examples: list[str],
) -> str:
    lowered = primary_interest.lower().strip(". ")
    word_count = len(lowered.split())
    signal_count = len(methods) + len(application_domains) + len(reference_examples)

    if (
        lowered == "not specified"
        or lowered in VAGUE_PHRASES
        or word_count < 5
        or (word_count < 8 and signal_count < 2)
        or (word_count < 12 and signal_count == 0)
    ):
        return "low"
    if word_count < 18 or signal_count < 3:
        return "medium"
    return "high"


def _followup_question(raw_student: dict[str, Any], normalized: dict[str, Any]) -> str:
    methods = normalized.get("research_methods") or []
    domains = normalized.get("application_domains") or []
    references = normalized.get("structured_facts", {}).get("reference_examples") or []

    if not methods:
        return "What methods or technical approaches are you most interested in, such as machine learning, NLP, computer vision, HCI, systems, or security?"
    if not domains:
        return "What application area are you hoping to work in, such as healthcare, education, climate, robotics, or social good?"
    if not references:
        return "Can you name a class, project, paper, or problem that reflects the kind of research you want to do?"
    return "What specific research question or problem would you most like to explore?"


def _clean_confidence(value: Any) -> str:
    cleaned = str(value or "low").lower().strip()
    if cleaned in {"high", "medium", "low"}:
        return cleaned
    return "low"


def _to_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _is_method(value: str) -> bool:
    lowered = value.lower()
    return lowered in METHOD_VOCAB


def _is_application(value: str) -> bool:
    lowered = value.lower()
    return lowered in APPLICATION_VOCAB
