from __future__ import annotations

from pydantic import BaseModel


class NamedCount(BaseModel):
    name: str
    count: int


class DiagnosticsSummary(BaseModel):
    counts: dict[str, int]
    total_by_school: list[NamedCount]
    eligible_by_school: list[NamedCount]
    generic_eligible_profiles: int
    source_system_counts: list[NamedCount]
