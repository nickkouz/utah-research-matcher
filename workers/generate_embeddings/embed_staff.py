from __future__ import annotations

from app.models.paper import Paper
from app.models.staff import StaffMatchProfile, StaffRegistry


def build_staff_summary_text(staff: StaffRegistry, profile: StaffMatchProfile) -> str:
    return (
        f"Researcher: {staff.name}. "
        f"Title: {staff.title or 'not specified'}. "
        f"Schools: {', '.join(staff.school_affiliations or []) or staff.primary_school or 'not specified'}. "
        f"Department: {staff.department or 'not specified'}. "
        f"Research summary: {profile.ai_research_summary}. "
        f"Research keywords: {', '.join(profile.research_keywords or []) or 'not specified'}. "
        f"Sector tags: {', '.join(profile.sector_tags or []) or 'not specified'}. "
        f"Technical tags: {', '.join(profile.technical_tags or []) or 'not specified'}."
    )


def build_staff_research_text(profile: StaffMatchProfile, papers: list[Paper]) -> str:
    paper_text = " ".join(
        filter(
            None,
            [
                f"{paper.title}. {paper.ai_summary or paper.abstract or ''}"
                for paper in papers[:15]
            ],
        )
    )
    return (
        f"Research profile: {profile.ai_research_summary}. "
        f"Research outputs: {paper_text}"
    )

