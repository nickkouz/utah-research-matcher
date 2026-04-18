from __future__ import annotations

import json

from app.models.paper import Paper
from app.services.llm_client import generate_structured_json, has_openai_client
from workers.enrich_research.tagging import infer_sector_tags, infer_technical_tags


def enrich_paper(paper: Paper) -> dict:
    if has_openai_client():
        payload = _model_paper_enrichment(paper)
        if payload:
            return payload
    text = " ".join(filter(None, [paper.title, paper.abstract]))
    return {
        "ai_summary": paper.abstract or paper.title,
        "sector_tags": infer_sector_tags(text),
        "technical_tags": infer_technical_tags(text),
    }


def _model_paper_enrichment(paper: Paper) -> dict | None:
    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["ai_summary", "sector_tags", "technical_tags"],
        "properties": {
            "ai_summary": {"type": "string"},
            "sector_tags": {"type": "array", "items": {"type": "string"}},
            "technical_tags": {"type": "array", "items": {"type": "string"}},
        },
    }
    return generate_structured_json(
        system_prompt="You summarize academic papers for research discovery.",
        user_prompt=json.dumps(
            {
                "title": paper.title,
                "year": paper.year,
                "abstract": paper.abstract,
                "venue": paper.venue,
            },
            indent=2,
        ),
        schema_name="paper_enrichment",
        json_schema=schema,
        temperature=0.1,
    )

