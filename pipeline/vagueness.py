from __future__ import annotations

from typing import Any


FOLLOWUP_MAP = {
    "low": "What research problem or application area are you most excited to explore?",
    "medium": "",
    "high": "",
}


def evaluate_vagueness(student_profile: dict[str, Any]) -> dict[str, Any]:
    confidence = student_profile.get("confidence", "low")
    needs_followup = confidence == "low"
    return {
        "needs_followup": needs_followup,
        "reason": (
            "Student interests are still too broad for confident matching."
            if needs_followup
            else "Student profile is specific enough for matching."
        ),
        "followup_question": FOLLOWUP_MAP[confidence],
    }
