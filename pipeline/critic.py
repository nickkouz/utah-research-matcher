from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pipeline.openai_client import generate_json


PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "05_critic.md"


def review_match(student_profile: dict[str, Any], match: dict[str, Any]) -> dict[str, Any]:
    prompt_result = _review_with_model(student_profile, match)
    if prompt_result:
        return prompt_result

    facts = student_profile["structured_facts"]
    skills = facts.get("skills", [])
    issues = []
    revised_rationale = None
    revised_emails = None

    rationale = match.get("rationale", "")
    if "strong fit" not in rationale.lower() and "align" not in rationale.lower():
        issues.append("Rationale is too generic.")
        revised_rationale = (
            f"{match['faculty']['name']} is a strong fit because the faculty profile and the student profile "
            "show direct overlap in research focus and current technical preparation."
        )

    email_payload = match.get("emails", {})
    lab_body = email_payload.get("lab_inquiry", {}).get("body", "")
    if skills and not any(skill in lab_body for skill in skills):
        issues.append("Lab inquiry email does not mention the student's relevant skills.")
        revised_emails = dict(email_payload)
        revised_lab = dict(revised_emails["lab_inquiry"])
        revised_lab["body"] = revised_lab["body"].replace(
            "My current background includes",
            "My current background, including " + ", ".join(skills) + ", includes",
            1,
        )
        revised_emails["lab_inquiry"] = revised_lab

    return {
        "faculty_id": match["faculty"]["id"],
        "approved": not issues,
        "issues": issues,
        "revised_rationale": revised_rationale,
        "revised_emails": revised_emails,
    }


def _review_with_model(student_profile: dict[str, Any], match: dict[str, Any]) -> dict[str, Any] | None:
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    payload = generate_json(
        system_prompt="You produce concise JSON only.",
        user_prompt=(
            f"{prompt}\n\n"
            f"Student profile JSON:\n{json.dumps(student_profile, indent=2)}\n\n"
            f"Match JSON:\n{json.dumps(match, indent=2)}"
        ),
    )
    if not payload:
        return None

    approved = bool(payload.get("approved"))
    issues = payload.get("issues")
    if not isinstance(issues, list):
        issues = []

    revised_rationale = payload.get("revised_rationale")
    if revised_rationale is not None:
        revised_rationale = str(revised_rationale).strip() or None

    revised_emails = payload.get("revised_emails")
    if revised_emails is not None and not isinstance(revised_emails, dict):
        revised_emails = None

    return {
        "faculty_id": str(payload.get("faculty_id") or match["faculty"]["id"]),
        "approved": approved,
        "issues": [str(issue) for issue in issues],
        "revised_rationale": revised_rationale,
        "revised_emails": revised_emails,
    }


def apply_reviews(matches: list[dict[str, Any]], reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_faculty_id = {review["faculty_id"]: review for review in reviews}
    for match in matches:
        review = by_faculty_id[match["faculty"]["id"]]
        if review["revised_rationale"]:
            match["rationale"] = review["revised_rationale"]
        if review["revised_emails"]:
            match["emails"] = review["revised_emails"]
    return matches
