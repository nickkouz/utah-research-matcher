from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.company import CompanyInterpretation
from app.schemas.staff import StaffSummaryResponse


class CompanyMatchResponse(BaseModel):
    company: CompanyInterpretation
    matches: list[StaffSummaryResponse] = Field(default_factory=list)

