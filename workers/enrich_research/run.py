from __future__ import annotations

import argparse

from sqlalchemy import select

from workers.common.db import worker_session
from workers.common.bootstrap import ensure_api_path
from workers.enrich_research.summarize_papers import enrich_paper
from workers.enrich_research.summarize_staff import enrich_staff_profile


ensure_api_path()

from app.models.paper import Paper  # noqa: E402
from app.models.staff import StaffMatchProfile, StaffRegistry  # noqa: E402

def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich staff and paper records with AI summaries and tags.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of staff profiles to enrich.")
    args = parser.parse_args()

    with worker_session() as session:
        rows = session.execute(
            select(StaffRegistry, StaffMatchProfile)
            .join(StaffMatchProfile, StaffRegistry.id == StaffMatchProfile.staff_id)
            .where(StaffRegistry.eligible_for_matching.is_(True))
            .order_by(StaffRegistry.name.asc())
        ).all()
        if args.limit:
            rows = rows[: args.limit]

        failures = 0
        for staff, profile in rows:
            try:
                papers = session.execute(
                    select(Paper).where(Paper.staff_id == staff.id).order_by(Paper.year.desc().nullslast())
                ).scalars().all()

                staff_payload = enrich_staff_profile(staff, profile, papers)
                profile.ai_research_summary = staff_payload["ai_research_summary"]
                profile.research_keywords = staff_payload["research_keywords"]
                profile.sector_tags = staff_payload["sector_tags"]
                profile.technical_tags = staff_payload["technical_tags"]
                session.add(profile)

                for paper in papers:
                    paper_payload = enrich_paper(paper)
                    paper.ai_summary = paper_payload["ai_summary"]
                    paper.sector_tags = paper_payload["sector_tags"]
                    paper.technical_tags = paper_payload["technical_tags"]
                    session.add(paper)
            except Exception:
                failures += 1

    print(f"Enriched staff summaries and paper summaries. Failures: {failures}.")


if __name__ == "__main__":
    main()
