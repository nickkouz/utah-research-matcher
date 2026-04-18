from __future__ import annotations

import argparse
import csv
from pathlib import Path
import re

from workers.common.bootstrap import ensure_api_path
from workers.common.db import worker_session
from workers.common.text import normalize_whitespace, slugify
from workers.enrich_research.tagging import extract_keywords, infer_sector_tags, infer_technical_tags


ensure_api_path()

from app.models.staff import StaffMatchProfile, StaffRegistry  # noqa: E402


DEFAULT_CSV_PATH = Path("data/raw/faculty_db.csv")
GENERIC_SUMMARY_HINTS = (
    "Biography and contact information",
    "Learn more at",
)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap staff data into Postgres from faculty_db.csv.")
    parser.add_argument("--csv-path", type=Path, default=DEFAULT_CSV_PATH, help="Path to the faculty CSV file.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of rows to import.")
    args = parser.parse_args()

    rows = _load_rows(args.csv_path, args.limit)
    with worker_session() as session:
        imported = 0
        for row in rows:
            staff = _upsert_staff(session, row)
            _upsert_match_profile(session, staff, row)
            imported += 1

    print(f"Imported or updated {imported} staff rows from CSV bootstrap.")


def _load_rows(path: Path, limit: int | None) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    if limit:
        return _balanced_subset(rows, limit)
    return rows


def _balanced_subset(rows: list[dict[str, str]], limit: int) -> list[dict[str, str]]:
    ranked = sorted(rows, key=_row_priority)
    buckets: dict[str, list[dict[str, str]]] = {}
    for row in ranked:
        school = normalize_whitespace(row.get("school")) or "Unknown"
        buckets.setdefault(school, []).append(row)

    ordered_schools = sorted(
        buckets,
        key=lambda school: (
            _row_priority(buckets[school][0]) if buckets[school] else (True, True, True, True, 1.0, school.lower()),
            school.lower(),
        ),
    )

    selected: list[dict[str, str]] = []
    while ordered_schools and len(selected) < limit:
        next_round: list[str] = []
        for school in ordered_schools:
            bucket = buckets[school]
            if not bucket:
                continue
            selected.append(bucket.pop(0))
            if len(selected) >= limit:
                break
            if bucket:
                next_round.append(school)
        ordered_schools = next_round

    return selected


def _row_priority(row: dict[str, str]) -> tuple[bool, bool, bool, bool, float, str]:
    summary = _best_summary(row)
    research_areas = _split_pipe_values(row.get("research_areas"))
    methods = _split_pipe_values(row.get("methods"))
    try:
        quality_score = float((row.get("quality_score") or "0").strip())
    except ValueError:
        quality_score = 0.0
    return (
        _is_generic_text(summary),
        not _has_publication_signal(row),
        not bool(research_areas),
        (row.get("source_type") or "").strip().lower() == "school-search-directory",
        -quality_score,
        normalize_whitespace(row.get("name")).lower(),
    )


def _upsert_staff(session, row: dict[str, str]) -> StaffRegistry:
    staff_id = normalize_whitespace(row.get("faculty_id")) or slugify(row.get("name"))
    staff = session.get(StaffRegistry, staff_id) or StaffRegistry(id=staff_id)

    school = normalize_whitespace(row.get("school"))
    department = normalize_whitespace(row.get("department"))
    bio = _best_bio(row)
    has_publication_signal = _has_publication_signal(row)
    summary = _best_summary(row)

    staff.profile_slug = staff_id
    staff.name = normalize_whitespace(row.get("name")) or staff.name
    staff.title = normalize_whitespace(row.get("title")) or None
    staff.email = normalize_whitespace(row.get("email")) or None
    staff.profile_url = normalize_whitespace(row.get("profile_url")) or ""
    staff.image_url = normalize_whitespace(row.get("image_url")) or None
    staff.lab_url = normalize_whitespace(row.get("lab_url")) or None
    staff.bio = bio or None
    staff.primary_school = school or None
    staff.school_affiliations = [school] if school else []
    staff.department = department or None
    staff.source_system = "faculty_db.csv"
    staff.has_publication_signal = has_publication_signal
    staff.eligible_for_matching = _eligible_for_matching(row, summary, has_publication_signal)
    session.add(staff)
    return staff


def _upsert_match_profile(session, staff: StaffRegistry, row: dict[str, str]) -> None:
    summary = _best_summary(row)
    if not summary:
        return

    profile = staff.match_profile or StaffMatchProfile(staff_id=staff.id, ai_research_summary=summary)
    research_keywords = _split_pipe_values(row.get("research_areas")) or extract_keywords(summary)
    methods = _split_pipe_values(row.get("methods"))
    active_signals = _split_pipe_values(row.get("active_signals"))
    profile.ai_research_summary = summary
    profile.research_keywords = research_keywords[:15]
    profile.technical_tags = (methods or infer_technical_tags(summary))[:12]
    profile.sector_tags = infer_sector_tags(summary)
    profile.publication_count = max(profile.publication_count or 0, len(active_signals))
    profile.last_active_year = _latest_year(row)
    profile.citation_count_total = profile.citation_count_total or 0
    session.add(profile)


def _best_summary(row: dict[str, str]) -> str:
    summary = normalize_whitespace(row.get("research_summary"))
    bio = _best_bio(row)
    if _is_generic_text(summary):
        summary = ""

    parts = [
        summary,
        normalize_whitespace(row.get("specific_field")),
        ", ".join(_split_pipe_values(row.get("research_areas"))),
        ", ".join(_split_pipe_values(row.get("methods"))),
        ", ".join(_split_pipe_values(row.get("current_projects"))),
    ]
    parts = [part for part in parts if part and not _is_generic_text(part)]
    if parts:
        candidate = " ".join(parts)
        return normalize_whitespace(candidate)

    candidate = bio if not _is_generic_text(bio) else ""
    if not candidate:
        return ""
    for hint in GENERIC_SUMMARY_HINTS:
        if candidate.startswith(hint):
            return bio or candidate
    return candidate


def _best_bio(row: dict[str, str]) -> str:
    return normalize_whitespace(row.get("bio")) or normalize_whitespace(row.get("research_summary"))


def _split_pipe_values(value: str | None) -> list[str]:
    items = []
    for item in (value or "").split("|"):
        cleaned = normalize_whitespace(item)
        if cleaned and cleaned not in items:
            items.append(cleaned)
    return items


def _has_publication_signal(row: dict[str, str]) -> bool:
    flags = (row.get("quality_flags") or "").lower()
    active_signals = normalize_whitespace(row.get("active_signals"))
    return ("missing_recent_publications" not in flags) or bool(active_signals)


def _eligible_for_matching(row: dict[str, str], summary: str, has_publication_signal: bool) -> bool:
    try:
        quality_score = float((row.get("quality_score") or "0").strip())
    except ValueError:
        quality_score = 0.0
    research_areas = _split_pipe_values(row.get("research_areas"))
    methods = _split_pipe_values(row.get("methods"))
    active_signals = _split_pipe_values(row.get("active_signals"))
    if _is_generic_text(summary):
        return False
    return bool(summary) and has_publication_signal and (
        quality_score >= 0.65
        or len(research_areas) >= 3
        or len(methods) >= 3
        or len(active_signals) >= 2
    )


def _is_generic_text(value: str | None) -> bool:
    text = normalize_whitespace(value).lower()
    if not text:
        return True
    generic_phrases = (
        "biography and contact information",
        "contact information for",
        "learn more at",
        "instructor at the university of utah",
    )
    if any(phrase in text for phrase in generic_phrases):
        return True
    return len(text.split()) < 8


def _latest_year(row: dict[str, str]) -> int | None:
    candidates = " ".join(
        filter(
            None,
            [
                normalize_whitespace(row.get("active_signals")),
                normalize_whitespace(row.get("current_projects")),
            ],
        )
    )
    years = [int(match.group(0)) for match in YEAR_RE.finditer(candidates)]
    if not years:
        return None
    return max(years)


if __name__ == "__main__":
    main()
