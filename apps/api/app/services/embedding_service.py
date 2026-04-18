from __future__ import annotations

from app.schemas.company import CompanyInterpretation
from app.services.llm_client import embed_text


def build_company_summary_text(company: CompanyInterpretation) -> str:
    return (
        f"Company: {company.company_name}. "
        f"Primary sector: {company.primary_sector}. "
        f"Subsector: {company.subsector or 'not specified'}. "
        f"Research need summary: {company.research_need_summary}. "
        f"School affinities: {', '.join(company.school_affinities) or 'not specified'}."
    )


def build_company_theme_text(company: CompanyInterpretation) -> str:
    return (
        f"Technical themes: {', '.join(company.technical_themes) or 'not specified'}. "
        f"Products and services: {', '.join(company.products_services) or 'not specified'}. "
        f"Market keywords: {', '.join(company.market_keywords) or 'not specified'}."
    )


def company_query_embeddings(company: CompanyInterpretation) -> tuple[list[float], list[float]]:
    return (
        embed_text(build_company_summary_text(company)),
        embed_text(build_company_theme_text(company)),
    )

