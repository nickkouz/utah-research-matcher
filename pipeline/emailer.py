from __future__ import annotations

from typing import Any


def build_rationale(student_profile: dict[str, Any], match: dict[str, Any]) -> str:
    faculty = match["faculty"]
    overlap = match.get("overlap_terms") or []
    overlap_text = ", ".join(overlap) if overlap else "related research interests"
    return (
        f"{faculty['name']}'s work in {faculty['bio'].rstrip('.').lower()} aligns with the student's profile "
        f"through {overlap_text}. The faculty profile also shows recent activity that supports outreach for current research opportunities."
    )


def generate_email_modes(student: dict[str, Any], match: dict[str, Any]) -> dict[str, dict[str, str]]:
    faculty = match["faculty"]
    facts = student["structured_facts"]
    summary = student["research_summary"]
    name = facts["name"]
    major = facts["major"]
    year = facts["year"]
    skills = ", ".join(facts["skills"]) if facts["skills"] else "basic technical skills"

    intro = f"My name is {name}, and I am a {year.lower()} majoring in {major} at the University of Utah."
    interest = f"I am seeking undergraduate research experience related to {summary.split('.', 1)[0].replace('Undergraduate in ' + major + ' seeking research experience in ', '')}."
    faculty_line = f"I was especially interested in your work because your profile highlights {faculty['bio'].rstrip('.').lower()}."
    skills_line = f"My current background includes {skills}, and I would be excited to contribute while continuing to learn."

    return {
        "coffee_chat": {
            "faculty_email": faculty["email"],
            "subject": f"Undergraduate interested in your research",
            "body": (
                f"Dear Professor {faculty['name'].split()[0]},\n\n"
                f"{intro} {interest} {faculty_line} "
                f"Would you be open to a short conversation about your lab and how an undergraduate might get involved? "
                f"{skills_line}\n\n"
                "Thank you for your time,\n"
                f"{name}"
            ),
        },
        "lab_inquiry": {
            "faculty_email": faculty["email"],
            "subject": f"Question about undergraduate research opportunities",
            "body": (
                f"Dear Professor {faculty['name'].split()[0]},\n\n"
                f"{intro} {interest} {faculty_line} "
                f"I am reaching out to ask whether you are open to working with undergraduates in your research group. "
                f"{skills_line}\n\n"
                "Thank you for considering my note,\n"
                f"{name}"
            ),
        },
        "paper_response": {
            "faculty_email": faculty["email"],
            "subject": f"Interested in your recent research direction",
            "body": (
                f"Dear Professor {faculty['name'].split()[0]},\n\n"
                f"{intro} {interest} {faculty_line} "
                f"I would love to learn more about the questions your group is currently exploring and whether there may be a way for an undergraduate to contribute. "
                f"{skills_line}\n\n"
                "Best regards,\n"
                f"{name}"
            ),
        },
    }


def attach_outputs(student_profile: dict[str, Any], matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for match in matches:
        match["rationale"] = build_rationale(student_profile, match)
        match["emails"] = generate_email_modes(student_profile, match)
    return matches
