from __future__ import annotations

import json
from pathlib import Path

from pipeline.emailer import attach_outputs
from pipeline.normalizer import load_student, normalize_student_profile
from pipeline.ranker import load_faculty_db, top_matches


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RESULTS_PATH = DATA_DIR / "demo_results.json"


def run_pipeline(student_path: Path | None = None, faculty_path: Path | None = None) -> dict:
    student_raw = load_student(student_path or DATA_DIR / "demo_student.json")
    faculty_records = load_faculty_db(faculty_path or DATA_DIR / "fallback_db.json")

    student_profile = normalize_student_profile(student_raw)
    matches = top_matches(student_profile, faculty_records, limit=5)
    matches = attach_outputs(student_profile, matches)

    result = {"student": student_profile, "matches": matches}
    RESULTS_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    result = run_pipeline()
    print(json.dumps(result, indent=2))
