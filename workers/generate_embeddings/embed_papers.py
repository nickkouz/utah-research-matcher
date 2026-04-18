from __future__ import annotations

from app.models.paper import Paper


def build_paper_embedding_text(paper: Paper) -> str:
    return (
        f"Title: {paper.title}. "
        f"Venue: {paper.venue or 'not specified'}. "
        f"Abstract: {paper.abstract or 'not specified'}. "
        f"Summary: {paper.ai_summary or 'not specified'}. "
        f"Sector tags: {', '.join(paper.sector_tags or []) or 'not specified'}. "
        f"Technical tags: {', '.join(paper.technical_tags or []) or 'not specified'}."
    )

