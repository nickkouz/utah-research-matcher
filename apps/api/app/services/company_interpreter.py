from __future__ import annotations

from pydantic import ValidationError

from app.schemas.company import CompanyInterpretation, CompanyInput
from app.services.llm_client import generate_structured_json


def interpret_company_input(payload: CompanyInput) -> CompanyInterpretation:
    structured = _interpret_with_model(payload)
    if structured:
        return structured
    return _interpret_with_rules(payload)


def _interpret_with_model(payload: CompanyInput) -> CompanyInterpretation | None:
    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "company_name",
            "ticker",
            "primary_sector",
            "subsector",
            "products_services",
            "technical_themes",
            "market_keywords",
            "research_need_summary",
            "school_affinities",
            "confidence",
        ],
        "properties": {
            "company_name": {"type": "string"},
            "ticker": {"type": ["string", "null"]},
            "primary_sector": {"type": "string"},
            "subsector": {"type": ["string", "null"]},
            "products_services": {"type": "array", "items": {"type": "string"}},
            "technical_themes": {"type": "array", "items": {"type": "string"}},
            "market_keywords": {"type": "array", "items": {"type": "string"}},
            "research_need_summary": {"type": "string"},
            "school_affinities": {"type": "array", "items": {"type": "string"}},
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        },
    }
    result = generate_structured_json(
        system_prompt=(
            "You convert public-company descriptions into structured research discovery queries. "
            "Infer a single primary sector and grounded technical themes only from the company input."
        ),
        user_prompt=(
            f"Company name: {payload.company_name}\n"
            f"Ticker: {payload.ticker or 'not specified'}\n"
            f"Description: {payload.company_description}\n\n"
            "Return a research-facing company interpretation suitable for University of Utah researcher matching."
        ),
        schema_name="company_interpretation",
        json_schema=schema,
    )
    if not result:
        return None
    try:
        return CompanyInterpretation.model_validate(result)
    except ValidationError:
        return None


def _interpret_with_rules(payload: CompanyInput) -> CompanyInterpretation:
    description = payload.company_description.lower()
    sector = "General Technology"
    school_affinities = ["College of Engineering"]
    themes = ["technology strategy"]

    keyword_map = [
        ("health", "Healthcare Technology", ["machine learning", "clinical data"], ["School of Medicine", "College of Engineering"]),
        ("medical", "Healthcare Technology", ["medical devices", "clinical systems"], ["School of Medicine", "College of Engineering"]),
        ("energy", "Energy", ["power systems", "sustainability"], ["College of Engineering"]),
        ("finance", "Financial Technology", ["data systems", "modeling"], ["David Eccles School of Business", "College of Engineering"]),
        ("robot", "Robotics", ["robotics", "autonomy"], ["College of Engineering"]),
        ("education", "Education Technology", ["learning systems", "analytics"], ["College of Education", "College of Engineering"]),
    ]

    for token, token_sector, token_themes, token_schools in keyword_map:
        if token in description:
            sector = token_sector
            themes = token_themes
            school_affinities = token_schools
            break

    products_services = [segment.strip() for segment in payload.company_description.split(",") if segment.strip()][:4]
    return CompanyInterpretation(
        company_name=payload.company_name,
        ticker=payload.ticker,
        primary_sector=sector,
        subsector=None,
        products_services=products_services,
        technical_themes=themes,
        market_keywords=themes,
        research_need_summary=(
            f"Public company in {sector} with themes in {', '.join(themes)}. "
            f"The organization is relevant for University of Utah researchers working across {', '.join(school_affinities)}."
        ),
        school_affinities=school_affinities,
        confidence="medium",
    )
