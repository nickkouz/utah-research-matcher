from __future__ import annotations

import json

from app.schemas.company import CompanyInterpretation
from app.schemas.staff import StaffSummaryResponse
from app.services.llm_client import generate_structured_json, has_openai_client


def rerank_candidates(
    company: CompanyInterpretation,
    candidates: list[StaffSummaryResponse],
) -> list[StaffSummaryResponse]:
    if not candidates or not has_openai_client():
        return candidates

    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["ranking"],
        "properties": {
            "ranking": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["staff_id", "score_adjustment", "match_reason", "key_outreach_points"],
                    "properties": {
                        "staff_id": {"type": "string"},
                        "score_adjustment": {"type": "number"},
                        "match_reason": {"type": "string"},
                        "key_outreach_points": {"type": "array", "items": {"type": "string"}},
                    },
                },
            }
        },
    }
    result = generate_structured_json(
        system_prompt=(
            "You rerank University of Utah researchers for company fit. "
            "Ground every decision in the candidate evidence only."
        ),
        user_prompt=(
            f"Company:\n{company.model_dump_json(indent=2)}\n\n"
            f"Candidates:\n{json.dumps([candidate.model_dump() for candidate in candidates], indent=2)}"
        ),
        schema_name="company_staff_rerank",
        json_schema=schema,
        temperature=0.05,
    )
    if not result:
        return candidates

    by_id = {candidate.staff_id: candidate for candidate in candidates}
    reranked: list[StaffSummaryResponse] = []
    seen: set[str] = set()
    for item in result.get("ranking", []):
        staff_id = str(item.get("staff_id") or "")
        candidate = by_id.get(staff_id)
        if candidate is None or staff_id in seen:
            continue
        reranked.append(
            candidate.model_copy(
                update={
                    "score": round(candidate.score + float(item.get("score_adjustment") or 0), 4),
                    "match_reason": str(item.get("match_reason") or candidate.match_reason),
                    "key_outreach_points": item.get("key_outreach_points") or candidate.key_outreach_points,
                }
            )
        )
        seen.add(staff_id)

    for candidate in candidates:
        if candidate.staff_id not in seen:
            reranked.append(candidate)

    reranked.sort(key=lambda item: item.score, reverse=True)
    return reranked

