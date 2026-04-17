from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pipeline.orchestrator import run_pipeline_for_student


ROOT = Path(__file__).resolve().parents[1]
EVAL_CASES_PATH = ROOT / "evals" / "match_eval_cases.json"


def run_eval(eval_cases_path: Path = EVAL_CASES_PATH) -> dict[str, Any]:
    cases = json.loads(eval_cases_path.read_text(encoding="utf-8"))
    total = len(cases)
    top1_hits = 0
    top3_hits = 0
    top5_hits = 0
    per_case = []

    for case in cases:
        result = run_pipeline_for_student(case["student"])
        if result.get("status") != "ready":
            per_case.append(
                {
                    "id": case["id"],
                    "status": result.get("status"),
                    "matched_faculty_ids": [],
                }
            )
            continue

        matched_ids = [match["faculty"]["id"] for match in result.get("matches", [])]
        acceptable_ids = set(case["acceptable_faculty_ids"])
        top1 = bool(matched_ids[:1] and matched_ids[0] in acceptable_ids)
        top3 = any(faculty_id in acceptable_ids for faculty_id in matched_ids[:3])
        top5 = any(faculty_id in acceptable_ids for faculty_id in matched_ids[:5])
        top1_hits += int(top1)
        top3_hits += int(top3)
        top5_hits += int(top5)

        per_case.append(
            {
                "id": case["id"],
                "status": "ready",
                "acceptable_faculty_ids": case["acceptable_faculty_ids"],
                "matched_faculty_ids": matched_ids,
                "top1_hit": top1,
                "top3_hit": top3,
                "top5_hit": top5,
            }
        )

    return {
        "total_cases": total,
        "top1_accuracy": round(top1_hits / total, 3) if total else 0.0,
        "top3_recall": round(top3_hits / total, 3) if total else 0.0,
        "top5_recall": round(top5_hits / total, 3) if total else 0.0,
        "cases": per_case,
    }


if __name__ == "__main__":
    print(json.dumps(run_eval(), indent=2))
