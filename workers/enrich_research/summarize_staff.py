from __future__ import annotations

import json

from app.models.paper import Paper
from app.models.staff import StaffMatchProfile, StaffRegistry
from app.services.llm_client import generate_structured_json, has_openai_client
from workers.enrich_research.tagging import extract_keywords, infer_sector_tags, infer_technical_tags


def enrich_staff_profile(staff: StaffRegistry, profile: StaffMatchProfile, papers: list[Paper]) -> dict:
    if has_openai_client():
        generated = _model_staff_enrichment(staff, profile, papers)
        if generated:
            return generated

    text = " ".join(
        filter(
            None,
            [
                staff.bio or "",
                profile.ai_research_summary or "",
                " ".join(paper.title for paper in papers[:10]),
            ],
        )
    )
    return {
        "ai_research_summary": (staff.bio or profile.ai_research_summary or f"Research profile for {staff.name}").strip(),
        "research_keywords": extract_keywords(text),
        "sector_tags": infer_sector_tags(text),
        "technical_tags": infer_technical_tags(text),
    }


def _model_staff_enrichment(staff: StaffRegistry, profile: StaffMatchProfile, papers: list[Paper]) -> dict | None:
    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["ai_research_summary", "research_keywords", "sector_tags", "technical_tags"],
        "properties": {
            "ai_research_summary": {"type": "string"},
            "research_keywords": {"type": "array", "items": {"type": "string"}},
            "sector_tags": {"type": "array", "items": {"type": "string"}},
            "technical_tags": {"type": "array", "items": {"type": "string"}},
        },
    }
    payload = generate_structured_json(
        system_prompt="You summarize University of Utah researcher profiles for company-to-researcher matching.",
        user_prompt=(
            f"Staff profile:\n{json.dumps({'name': staff.name, 'title': staff.title, 'bio': staff.bio, 'schools': staff.school_affiliations, 'department': staff.department}, indent=2)}\n\n"
            f"Recent papers:\n{json.dumps([{'title': paper.title, 'year': paper.year, 'abstract': paper.abstract} for paper in papers[:10]], indent=2)}"
        ),
        schema_name="staff_enrichment",
        json_schema=schema,
        temperature=0.1,
    )
    return payload

