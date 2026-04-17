from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pipeline.openai_client import generate_json


EMAIL_MODES = ("coffee_chat", "lab_inquiry", "paper_response")
PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "04_emailer.md"


def _professor_salutation(faculty_name: str) -> str:
    last_name = faculty_name.split()[-1] if faculty_name.strip() else "Professor"
    return f"Professor {last_name}"


def _interest_clause(student_profile: dict[str, Any]) -> str:
    summary = student_profile.get("research_summary", "")
    major = student_profile.get("structured_facts", {}).get("major", "not specified")
    prefix = f"Undergraduate in {major} seeking research experience in "
    first_sentence = summary.split(".", 1)[0]
    return first_sentence.replace(prefix, "").strip() or "the research areas described in my profile"


def _clean_bio_phrase(bio: str) -> str:
    text = bio.strip().rstrip(".")
    lowered = text.lower()
    prefixes = (
        "research interests in ",
        "research interests include ",
        "research focuses on ",
        "research focus includes ",
    )
    for prefix in prefixes:
        if lowered.startswith(prefix):
            return text[len(prefix) :].strip()
    return text


def generate_email_modes(student_profile: dict[str, Any], match: dict[str, Any]) -> dict[str, Any]:
    prompt_result = _generate_emails_with_model(student_profile, match)
    if prompt_result:
        return prompt_result

    faculty = match["faculty"]
    facts = student_profile["structured_facts"]
    salutation = _professor_salutation(faculty["name"])
    name = facts["name"]
    major = facts["major"]
    year = facts["year"]
    skills = facts["skills"]
    skills_text = ", ".join(skills) if skills else "my current coursework and technical background"
    interest_area = _interest_clause(student_profile)
    faculty_focus = _clean_bio_phrase(faculty["bio"])

    intro = f"My name is {name}, and I am a {year.lower()} majoring in {major} at the University of Utah."
    interest_sentence = f"I am looking for undergraduate research experience in {interest_area}."
    faculty_sentence = f"I was especially interested in your work because your profile highlights {faculty_focus.lower()}."
    skills_sentence = f"My current background includes {skills_text}, and I would be excited to contribute while continuing to learn."

    emails = {
        "coffee_chat": {
            "subject": "Undergraduate interested in your research",
            "body": (
                f"Dear {salutation},\n\n"
                f"{intro} {interest_sentence} {faculty_sentence} "
                "Would you be open to a short conversation about your research and how an undergraduate might get involved? "
                f"{skills_sentence}\n\n"
                "Thank you for your time,\n"
                f"{name}"
            ),
            "faculty_email": faculty["email"],
        },
        "lab_inquiry": {
            "subject": "Question about undergraduate research opportunities",
            "body": (
                f"Dear {salutation},\n\n"
                f"{intro} {interest_sentence} {faculty_sentence} "
                "I am reaching out to ask whether you are currently open to working with undergraduates in your group. "
                f"{skills_sentence}\n\n"
                "Thank you for considering my note,\n"
                f"{name}"
            ),
            "faculty_email": faculty["email"],
        },
        "paper_response": {
            "subject": "Interested in your recent research direction",
            "body": (
                f"Dear {salutation},\n\n"
                f"{intro} {interest_sentence} {faculty_sentence} "
                "I would love to learn more about the questions your group is currently exploring and whether there may be a way for an undergraduate to contribute. "
                f"{skills_sentence}\n\n"
                "Best regards,\n"
                f"{name}"
            ),
            "faculty_email": faculty["email"],
        },
    }
    return {"faculty_id": faculty["id"], "emails": emails}


def _generate_emails_with_model(student_profile: dict[str, Any], match: dict[str, Any]) -> dict[str, Any] | None:
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    payload = generate_json(
        system_prompt="You produce concise JSON only.",
        user_prompt=(
            f"{prompt}\n\n"
            f"Student profile JSON:\n{json.dumps(student_profile, indent=2)}\n\n"
            f"Ranked match JSON:\n{json.dumps(match, indent=2)}"
        ),
    )
    if not payload:
        return None

    emails = payload.get("emails")
    if not isinstance(emails, dict):
        return None

    normalized_emails = {}
    for mode in EMAIL_MODES:
        email = emails.get(mode)
        if not isinstance(email, dict):
            return None
        subject = str(email.get("subject") or "").strip()
        body = str(email.get("body") or "").strip()
        faculty_email = str(email.get("faculty_email") or match["faculty"]["email"]).strip()
        if not subject or not body or not faculty_email:
            return None
        normalized_emails[mode] = {
            "subject": subject,
            "body": body,
            "faculty_email": faculty_email,
        }

    return {
        "faculty_id": str(payload.get("faculty_id") or match["faculty"]["id"]),
        "emails": normalized_emails,
    }


def apply_email_payloads(matches: list[dict[str, Any]], email_payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_faculty_id = {payload["faculty_id"]: payload["emails"] for payload in email_payloads}
    for match in matches:
        match["emails"] = by_faculty_id[match["faculty"]["id"]]
    return matches
