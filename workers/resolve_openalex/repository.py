from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.staff import StaffMatchProfile, StaffRegistry
from app.services.openalex_service import OpenAlexAuthorCandidate


def upsert_author_match(
    session: Session,
    *,
    staff: StaffRegistry,
    author: OpenAlexAuthorCandidate,
) -> StaffMatchProfile:
    profile = staff.match_profile or StaffMatchProfile(staff_id=staff.id, ai_research_summary=staff.bio or staff.name)
    profile.openalex_author_id = author.author_id
    profile.publication_count = author.works_count
    profile.citation_count_total = author.cited_by_count
    counts_by_year = author.raw.get("counts_by_year") or []
    recent_years = [int(item.get("year")) for item in counts_by_year if item.get("year")]
    profile.last_active_year = max(recent_years) if recent_years else profile.last_active_year
    if not profile.ai_research_summary:
        profile.ai_research_summary = staff.bio or f"Research profile for {staff.name}"
    session.add(profile)

    staff.has_publication_signal = author.works_count >= 1
    staff.eligible_for_matching = author.works_count >= settings.minimum_publication_count
    session.add(staff)
    return profile
