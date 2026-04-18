from __future__ import annotations

from pydantic import BaseModel, Field


class CompanyInput(BaseModel):
    company_name: str = Field(min_length=2)
    ticker: str | None = None
    company_description: str = Field(min_length=20)


class CompanyInterpretation(BaseModel):
    company_name: str
    ticker: str | None = None
    primary_sector: str
    subsector: str | None = None
    products_services: list[str] = Field(default_factory=list)
    technical_themes: list[str] = Field(default_factory=list)
    market_keywords: list[str] = Field(default_factory=list)
    research_need_summary: str
    school_affinities: list[str] = Field(default_factory=list)
    confidence: str

