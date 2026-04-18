from __future__ import annotations

from dataclasses import dataclass
import re

from pydantic import ValidationError

from app.schemas.company import CompanyInterpretation, CompanyInput
from app.services.llm_client import generate_structured_json


GENERIC_SECTORS = {"general technology", "technology", "other", "unknown"}
GENERIC_THEMES = {"technology strategy", "innovation", "analytics"}


@dataclass(frozen=True)
class InterpretationHint:
    primary_sector: str
    subsector: str | None
    tokens: tuple[str, ...]
    technical_themes: tuple[str, ...]
    market_keywords: tuple[str, ...]
    school_affinities: tuple[str, ...]


INTERPRETATION_HINTS: tuple[InterpretationHint, ...] = (
    InterpretationHint(
        primary_sector="Biotechnology",
        subsector="Drug Discovery and Computational Biology",
        tokens=(
            "biotech",
            "biotechnology",
            "drug discovery",
            "therapeutic",
            "therapeutics",
            "pharma",
            "pharmaceutical",
            "genomics",
            "proteomics",
            "molecular biology",
            "cell biology",
            "wet lab",
        ),
        technical_themes=(
            "drug discovery",
            "computational biology",
            "machine learning",
            "automation",
            "biological data",
        ),
        market_keywords=("biotech", "drug discovery", "computational biology", "life sciences"),
        school_affinities=(
            "Spencer Fox Eccles School of Medicine",
            "College of Pharmacy",
            "College of Science",
            "College of Engineering",
        ),
    ),
    InterpretationHint(
        primary_sector="Healthcare Technology",
        subsector="Clinical Systems and Digital Health",
        tokens=(
            "healthcare",
            "digital health",
            "clinical",
            "patient",
            "hospital",
            "provider",
            "medical device",
            "diagnostic",
            "radiology",
            "pathology",
            "care delivery",
        ),
        technical_themes=(
            "clinical data",
            "decision support",
            "medical devices",
            "machine learning",
            "health informatics",
        ),
        market_keywords=("healthcare", "clinical systems", "patient care", "medical software"),
        school_affinities=(
            "Spencer Fox Eccles School of Medicine",
            "College of Nursing",
            "College of Pharmacy",
            "College of Engineering",
        ),
    ),
    InterpretationHint(
        primary_sector="Computing and AI",
        subsector="AI Platforms and Applied Machine Learning",
        tokens=(
            "artificial intelligence",
            "machine learning",
            "generative ai",
            "large language model",
            "llm",
            "computer vision",
            "natural language",
            "ai platform",
            "model training",
            "agentic",
        ),
        technical_themes=(
            "machine learning",
            "large language models",
            "computer vision",
            "natural language processing",
            "data systems",
        ),
        market_keywords=("ai", "machine learning", "software platform", "data infrastructure"),
        school_affinities=("Kahlert School of Computing", "College of Engineering", "College of Science"),
    ),
    InterpretationHint(
        primary_sector="Energy",
        subsector="Grid, Storage, and Energy Systems",
        tokens=(
            "energy",
            "battery",
            "grid",
            "power",
            "solar",
            "wind",
            "utility",
            "electrification",
            "storage",
            "dispatch",
        ),
        technical_themes=("power systems", "energy forecasting", "optimization", "batteries", "control systems"),
        market_keywords=("energy", "grid software", "storage", "power systems"),
        school_affinities=("College of Engineering", "College of Science"),
    ),
    InterpretationHint(
        primary_sector="Financial Technology",
        subsector="Financial Analytics and Risk Systems",
        tokens=(
            "fintech",
            "finance",
            "bank",
            "banking",
            "insurance",
            "credit",
            "payments",
            "fraud",
            "trading",
            "risk",
        ),
        technical_themes=("risk modeling", "analytics", "data systems", "forecasting", "optimization"),
        market_keywords=("finance", "fintech", "risk", "decision systems"),
        school_affinities=("David Eccles School of Business", "Kahlert School of Computing", "College of Engineering"),
    ),
    InterpretationHint(
        primary_sector="Robotics",
        subsector="Autonomy and Intelligent Systems",
        tokens=(
            "robot",
            "robotics",
            "autonomy",
            "autonomous",
            "drone",
            "sensor fusion",
            "control systems",
            "perception",
            "manipulation",
        ),
        technical_themes=("robotics", "autonomy", "control systems", "computer vision", "sensor systems"),
        market_keywords=("robotics", "autonomy", "sensing", "intelligent systems"),
        school_affinities=("College of Engineering", "Kahlert School of Computing"),
    ),
    InterpretationHint(
        primary_sector="Cybersecurity",
        subsector="Security and Privacy Systems",
        tokens=(
            "cybersecurity",
            "security",
            "privacy",
            "identity",
            "threat",
            "malware",
            "encryption",
            "cryptography",
            "zero trust",
        ),
        technical_themes=("security", "privacy", "cryptography", "systems", "machine learning"),
        market_keywords=("security", "privacy", "cyber", "risk"),
        school_affinities=("Kahlert School of Computing", "College of Engineering"),
    ),
)


def interpret_company_input(payload: CompanyInput) -> CompanyInterpretation:
    structured = _interpret_with_model(payload)
    if structured:
        return _strengthen_interpretation(payload, structured)
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
    hint = _best_hint(payload.company_description)
    sector = hint.primary_sector if hint else "General Technology"
    subsector = hint.subsector if hint else None
    themes = list(hint.technical_themes) if hint else ["technology strategy", "data systems"]
    market_keywords = list(hint.market_keywords) if hint else list(themes)
    school_affinities = list(hint.school_affinities) if hint else ["College of Engineering"]
    products_services = _extract_products_services(payload.company_description)
    return CompanyInterpretation(
        company_name=payload.company_name,
        ticker=payload.ticker,
        primary_sector=sector,
        subsector=subsector,
        products_services=products_services,
        technical_themes=themes,
        market_keywords=market_keywords,
        research_need_summary=_compose_summary(sector, subsector, products_services, themes, school_affinities),
        school_affinities=school_affinities,
        confidence="medium",
    )


def _strengthen_interpretation(
    payload: CompanyInput,
    interpretation: CompanyInterpretation,
) -> CompanyInterpretation:
    hint = _best_hint(payload.company_description)
    products_services = interpretation.products_services or _extract_products_services(payload.company_description)
    technical_themes = interpretation.technical_themes
    market_keywords = interpretation.market_keywords
    school_affinities = interpretation.school_affinities
    primary_sector = interpretation.primary_sector
    subsector = interpretation.subsector
    confidence = interpretation.confidence

    if hint:
        if interpretation.primary_sector.strip().lower() in GENERIC_SECTORS:
            primary_sector = hint.primary_sector
        if not interpretation.subsector:
            subsector = hint.subsector
        technical_themes = _merge_unique(technical_themes, hint.technical_themes)
        market_keywords = _merge_unique(market_keywords, hint.market_keywords, technical_themes)
        school_affinities = _merge_unique(school_affinities, hint.school_affinities)
        if confidence == "low":
            confidence = "medium"

    if not technical_themes or set(theme.lower() for theme in technical_themes) <= GENERIC_THEMES:
        technical_themes = _merge_unique(technical_themes, _extract_themes(payload.company_description))
    if not market_keywords:
        market_keywords = _merge_unique(technical_themes, products_services)
    if not school_affinities:
        school_affinities = _default_schools_for_sector(primary_sector)

    summary = interpretation.research_need_summary
    if _looks_generic_summary(summary, technical_themes):
        summary = _compose_summary(primary_sector, subsector, products_services, technical_themes, school_affinities)

    return interpretation.model_copy(
        update={
            "primary_sector": primary_sector,
            "subsector": subsector,
            "products_services": products_services,
            "technical_themes": technical_themes,
            "market_keywords": market_keywords,
            "school_affinities": school_affinities,
            "research_need_summary": summary,
            "confidence": confidence,
        }
    )


def _best_hint(description: str) -> InterpretationHint | None:
    lowered = description.lower()
    ranked: list[tuple[int, InterpretationHint]] = []
    for hint in INTERPRETATION_HINTS:
        score = sum(1 for token in hint.tokens if token in lowered)
        if score:
            ranked.append((score, hint))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (-item[0], item[1].primary_sector))
    return ranked[0][1]


def _extract_products_services(description: str) -> list[str]:
    chunks = [
        chunk.strip()
        for chunk in re.split(r"[.;,]", description)
        if chunk.strip()
    ]
    unique: list[str] = []
    for chunk in chunks:
        if chunk not in unique:
            unique.append(chunk)
    return unique[:4]


def _extract_themes(description: str) -> list[str]:
    lowered = description.lower()
    theme_map = {
        "machine learning": ("machine learning", "artificial intelligence", "deep learning"),
        "large language models": ("large language model", "llm", "generative ai"),
        "computer vision": ("computer vision", "imaging", "image analysis"),
        "natural language processing": ("natural language", "text mining", "nlp"),
        "drug discovery": ("drug discovery", "therapeutic", "pharmaceutical"),
        "computational biology": ("genomics", "proteomics", "computational biology", "bioinformatics"),
        "automation": ("automation", "robotic lab", "automated experiments", "high-throughput"),
        "clinical data": ("clinical", "patient", "ehr", "medical record"),
        "data systems": ("data platform", "data infrastructure", "analytics", "data systems"),
        "optimization": ("optimization", "forecasting", "scheduling"),
    }
    themes = [theme for theme, tokens in theme_map.items() if any(token in lowered for token in tokens)]
    return themes[:6] or ["data systems"]


def _default_schools_for_sector(primary_sector: str) -> list[str]:
    sector_map = {
        "Biotechnology": [
            "Spencer Fox Eccles School of Medicine",
            "College of Pharmacy",
            "College of Science",
            "College of Engineering",
        ],
        "Healthcare Technology": [
            "Spencer Fox Eccles School of Medicine",
            "College of Nursing",
            "College of Engineering",
        ],
        "Financial Technology": ["David Eccles School of Business", "Kahlert School of Computing", "College of Engineering"],
        "Robotics": ["College of Engineering", "Kahlert School of Computing"],
        "Cybersecurity": ["Kahlert School of Computing", "College of Engineering"],
    }
    return sector_map.get(primary_sector, ["College of Engineering"])


def _compose_summary(
    primary_sector: str,
    subsector: str | None,
    products_services: list[str],
    technical_themes: list[str],
    school_affinities: list[str],
) -> str:
    return (
        f"Public company in {primary_sector}"
        f"{f' focused on {subsector}' if subsector else ''}, "
        f"with products or capabilities in {', '.join(products_services[:3]) or 'research-intensive operations'}. "
        f"Relevant research themes include {', '.join(technical_themes[:5]) or 'data systems and applied research'}. "
        f"This maps most strongly to University of Utah researchers across {', '.join(school_affinities[:4])}."
    )


def _looks_generic_summary(summary: str, technical_themes: list[str]) -> bool:
    lowered = summary.lower().strip()
    if not lowered:
        return True
    if any(sector in lowered for sector in GENERIC_SECTORS) and not technical_themes:
        return True
    return "technology strategy" in lowered or "general technology" in lowered


def _merge_unique(*groups: list[str] | tuple[str, ...]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for item in group:
            cleaned = item.strip()
            if not cleaned:
                continue
            lowered = cleaned.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            merged.append(cleaned)
    return merged[:8]
