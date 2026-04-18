from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.paper import PaperSummary


class CollaboratorSummary(BaseModel):
    name: str
    affiliation: str | None = None
    is_uofu: bool = False
    profile_url: str | None = None
    related_papers: list[str] = Field(default_factory=list)


class StaffSummaryResponse(BaseModel):
    staff_id: str
    name: str
    title: str | None = None
    primary_school: str | None = None
    school_affiliations: list[str] = Field(default_factory=list)
    department: str | None = None
    ai_research_summary: str
    match_reason: str
    score: float
    recent_papers: list[PaperSummary] = Field(default_factory=list)
    most_cited_papers: list[PaperSummary] = Field(default_factory=list)
    key_outreach_points: list[str] = Field(default_factory=list)
    further_contacts: list[CollaboratorSummary] = Field(default_factory=list)


class StaffDetailResponse(BaseModel):
    staff_id: str
    name: str
    title: str | None = None
    email: str | None = None
    profile_url: str
    primary_school: str | None = None
    school_affiliations: list[str] = Field(default_factory=list)
    department: str | None = None
    bio: str | None = None
    ai_research_summary: str
    recent_papers: list[PaperSummary] = Field(default_factory=list)
    most_cited_papers: list[PaperSummary] = Field(default_factory=list)
    searchable_papers_count: int = 0
    key_outreach_points: list[str] = Field(default_factory=list)
    collaborators: list[CollaboratorSummary] = Field(default_factory=list)


class CollaboratorResponse(BaseModel):
    staff_id: str
    collaborators: list[CollaboratorSummary] = Field(default_factory=list)

