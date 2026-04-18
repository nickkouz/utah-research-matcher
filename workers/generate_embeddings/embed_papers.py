from __future__ import annotations

from app.models.paper import Paper


def build_paper_embedding_text(paper: Paper) -> str:
    abstract = _truncate(paper.abstract or "", 2400)
    summary = _truncate(paper.ai_summary or "", 1200)
    return (
        f"Title: {paper.title}. "
        f"Abstract-first research description: {abstract or 'not specified'}. "
        f"AI summary: {summary or 'not specified'}. "
        f"Venue: {paper.venue or 'not specified'}. "
        f"Publication year: {paper.year or 'not specified'}. "
        f"Sector tags: {', '.join(paper.sector_tags or []) or 'not specified'}. "
        f"Technical tags: {', '.join(paper.technical_tags or []) or 'not specified'}."
    )


def _truncate(text: str, limit: int) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."
