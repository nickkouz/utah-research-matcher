from __future__ import annotations

from typing import Any


def evaluate_vagueness(student_profile: dict[str, Any]) -> dict[str, Any]:
    confidence = str(student_profile.get("confidence", "low")).lower()
    needs_followup = confidence == "low"
    return {
        "needs_followup": needs_followup,
        "reason": (
            "Student interests are still too broad for confident faculty matching."
            if needs_followup
            else "Student profile is specific enough to proceed with ranking."
        ),
        "followup_question": str(student_profile.get("followup_question") or ""),
    }
