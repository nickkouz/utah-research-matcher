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
    abstract_rich_papers = [paper for paper in papers if paper.abstract]
    fallback_papers = [paper for paper in papers if not paper.abstract]
    selected_papers = (abstract_rich_papers[:18] + fallback_papers[:6])[:24]
    paper_text = " ".join(
        filter(None, [_paper_research_context(paper) for paper in selected_papers])
    )
    return (
        f"Research profile: {profile.ai_research_summary}. "
        f"Research keywords: {', '.join(profile.research_keywords or []) or 'not specified'}. "
        f"Technical themes: {', '.join(profile.technical_tags or []) or 'not specified'}. "
        f"Research outputs: {paper_text}"
    )


def _paper_research_context(paper: Paper) -> str:
    abstract = _truncate(paper.abstract or "", 1200)
    summary = _truncate(paper.ai_summary or "", 500)
    parts = [f"Paper: {paper.title}."]
    if abstract:
        parts.append(f"Abstract: {abstract}.")
    elif summary:
        parts.append(f"Summary: {summary}.")
    if paper.technical_tags:
        parts.append(f"Themes: {', '.join(paper.technical_tags[:6])}.")
    return " ".join(parts)


def _truncate(text: str, limit: int) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."
