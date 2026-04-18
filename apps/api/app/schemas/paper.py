from __future__ import annotations

from pydantic import BaseModel, Field


class PaperSummary(BaseModel):
    id: str
    title: str
    year: int | None = None
    venue: str | None = None
    citation_count: int = 0
    paper_url: str | None = None
    pdf_url: str | None = None
    ai_summary: str | None = None


class PaperListResponse(BaseModel):
    staff_id: str
    total: int
    items: list[PaperSummary] = Field(default_factory=list)

