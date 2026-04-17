from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
PRIMARY_FACULTY_DB_PATH = DATA_DIR / "faculty_db.json"
FALLBACK_FACULTY_DB_PATH = DATA_DIR / "fallback_db.json"
FACULTY_BROWSER_PATH = DATA_DIR / "faculty_browser.json"

TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z\-]+")
STOPWORDS = {
    "a",
    "about",
    "an",
    "and",
    "applications",
    "approach",
    "are",
    "at",
    "for",
    "focus",
    "focusing",
    "in",
    "include",
    "includes",
    "interests",
    "is",
    "lab",
    "learning",
    "of",
    "on",
    "professor",
    "research",
    "systems",
    "the",
    "to",
    "using",
    "with",
    "work",
}
HIGH_SIGNAL_METHODS = {
    "artificial intelligence",
    "clinical text",
    "computer architecture",
    "computer security",
    "computer vision",
    "deep learning",
    "education",
    "healthcare",
    "high performance computing",
    "human computer interaction",
    "human-computer interaction",
    "language models",
    "machine learning",
    "multimodal learning",
    "natural language processing",
    "nlp",
    "reasoning",
    "representation learning",
    "robotics",
    "security",
    "social good",
    "structured prediction",
    "systems",
    "text understanding",
    "trustworthy ai",
}


def resolve_faculty_dataset_path() -> Path:
    if PRIMARY_FACULTY_DB_PATH.exists():
        return PRIMARY_FACULTY_DB_PATH
    return FALLBACK_FACULTY_DB_PATH


def load_faculty_db(path: str | Path | None = None) -> list[dict[str, Any]]:
    resolved = Path(path) if path else resolve_faculty_dataset_path()
    records = json.loads(resolved.read_text(encoding="utf-8"))
    return [normalize_faculty_record(record) for record in records]


def normalize_faculty_record(record: dict[str, Any]) -> dict[str, Any]:
    bio = str(record.get("bio") or "not specified").strip()
    recent_papers = record.get("recent_papers") or []
    research_text = str(record.get("research_text") or bio or "").strip()
    normalized_summary = str(
        record.get("normalized_research_summary") or _build_summary_from_faculty(record)
    ).strip()
    paper_titles_text = str(
        record.get("paper_titles_text") or " ".join(_paper_title_strings(recent_papers))
    ).strip()
    research_keywords = _clean_keywords(record.get("research_keywords")) or _derive_keywords(
        normalized_summary,
        research_text,
        paper_titles_text,
    )
    browser_snippet = str(
        record.get("browser_snippet") or _browser_snippet(normalized_summary, bio)
    ).strip()
    embedding_summary = _clean_embedding(record.get("embedding_summary") or record.get("embedding"))
    embedding_papers = _clean_embedding(record.get("embedding_papers"))

    faculty = {
        "id": str(record.get("id") or "not_specified"),
        "name": str(record.get("name") or "not specified"),
        "title": str(record.get("title") or "not specified"),
        "department": str(record.get("department") or "not specified"),
        "email": str(record.get("email") or "not specified"),
        "profile_url": str(record.get("profile_url") or ""),
        "bio": bio,
        "recent_papers": recent_papers,
        "research_text": research_text,
        "normalized_research_summary": normalized_summary,
        "research_keywords": research_keywords,
        "paper_titles_text": paper_titles_text,
        "embedding_summary": embedding_summary,
        "embedding_papers": embedding_papers,
        "embedding": embedding_summary,
        "browser_snippet": browser_snippet,
        "last_active_year": int(record.get("last_active_year") or _infer_last_active_year(recent_papers)),
        "accepts_undergrads": record.get("accepts_undergrads"),
    }
    faculty["eligible_for_matching"] = _is_match_eligible(faculty)
    return faculty


def build_faculty_browser_payload(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized_records = [normalize_faculty_record(record) for record in records]
    return [
        {
            "id": faculty["id"],
            "name": faculty["name"],
            "title": faculty["title"],
            "department": faculty["department"],
            "browser_snippet": faculty["browser_snippet"],
            "profile_url": faculty["profile_url"],
            "last_active_year": faculty["last_active_year"],
            "research_keywords": faculty["research_keywords"][:6],
            "accepts_undergrads": faculty["accepts_undergrads"],
            "eligible_for_matching": faculty["eligible_for_matching"],
        }
        for faculty in normalized_records
    ]


def write_faculty_browser_payload(
    source_path: str | Path | None = None,
    destination_path: str | Path = FACULTY_BROWSER_PATH,
) -> Path:
    records = load_faculty_db(source_path)
    payload = build_faculty_browser_payload(records)
    destination = Path(destination_path)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return destination


def _build_summary_from_faculty(record: dict[str, Any]) -> str:
    bio = str(record.get("bio") or "").strip()
    if bio and bio.lower() != "not specified":
        return bio.rstrip(".") + "."
    research_text = str(record.get("research_text") or "").strip()
    if research_text:
        return research_text.rstrip(".") + "."
    return "Research summary not specified."


def _paper_title_strings(recent_papers: list[dict[str, Any]]) -> list[str]:
    titles = []
    for paper in recent_papers:
        title = str(paper.get("title") or "").strip()
        if title:
            titles.append(title)
    return titles


def _clean_keywords(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        items = value.split(",")
    else:
        items = value
    cleaned = []
    for item in items:
        text = str(item).strip()
        if text and text.lower() not in {entry.lower() for entry in cleaned}:
            cleaned.append(text)
    return cleaned


def _derive_keywords(*texts: str) -> list[str]:
    joined = " ".join(text for text in texts if text)
    lowered = joined.lower()
    phrases = []
    for term in sorted(HIGH_SIGNAL_METHODS, key=len, reverse=True):
        if term in lowered:
            phrases.append(term)

    tokens = []
    for token in TOKEN_RE.findall(joined):
        lowered_token = token.lower()
        if lowered_token in STOPWORDS or len(lowered_token) < 4:
            continue
        if lowered_token not in tokens:
            tokens.append(lowered_token)

    keywords = phrases + tokens
    deduped = []
    seen = set()
    for keyword in keywords:
        key = keyword.lower()
        if key not in seen:
            deduped.append(keyword)
            seen.add(key)
    return deduped[:12]


def _clean_embedding(value: Any) -> list[float]:
    if not isinstance(value, list):
        return []
    cleaned = []
    for item in value:
        try:
            cleaned.append(float(item))
        except (TypeError, ValueError):
            return []
    return cleaned


def _browser_snippet(summary: str, bio: str) -> str:
    text = summary if summary and summary != "Research summary not specified." else bio
    first_sentence = text.split(".", 1)[0].strip()
    return first_sentence + "." if first_sentence else "Research focus not specified."


def _infer_last_active_year(recent_papers: list[dict[str, Any]]) -> int:
    years = []
    for paper in recent_papers:
        try:
            years.append(int(paper.get("year")))
        except (TypeError, ValueError):
            continue
    return max(years) if years else 0


def _is_match_eligible(faculty: dict[str, Any]) -> bool:
    if faculty["email"] == "not specified":
        return False
    summary_signal = faculty["normalized_research_summary"] and faculty["normalized_research_summary"] != "Research summary not specified."
    keyword_signal = len(faculty["research_keywords"]) >= 2
    activity_signal = faculty["last_active_year"] >= 2022 if faculty["last_active_year"] else False
    return bool(summary_signal and keyword_signal and activity_signal)
