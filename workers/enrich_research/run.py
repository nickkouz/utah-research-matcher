from __future__ import annotations

import argparse

from sqlalchemy import case, desc, func, or_, select

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
        paper_status = (
            select(
                Paper.staff_id.label("staff_id"),
                func.count(Paper.id).label("paper_count"),
                func.sum(
                    case(
                        (or_(Paper.ai_summary.is_(None), Paper.ai_summary == ""), 1),
                        else_=0,
                    )
                ).label("missing_paper_summaries"),
            )
            .group_by(Paper.staff_id)
            .subquery()
        )
        rows = session.execute(
            select(
                StaffRegistry,
                StaffMatchProfile,
                paper_status.c.paper_count,
                paper_status.c.missing_paper_summaries,
            )
            .join(StaffMatchProfile, StaffRegistry.id == StaffMatchProfile.staff_id)
            .outerjoin(paper_status, paper_status.c.staff_id == StaffRegistry.id)
            .where(StaffRegistry.eligible_for_matching.is_(True))
            .order_by(
                desc(
                    case(
                        (
                            or_(
                                StaffMatchProfile.ai_research_summary.is_(None),
                                StaffMatchProfile.ai_research_summary == "",
                                StaffMatchProfile.ai_research_summary.ilike("%biography and contact information%"),
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ),
                desc(func.coalesce(paper_status.c.missing_paper_summaries, 0)),
                desc(StaffMatchProfile.publication_count),
                desc(StaffMatchProfile.citation_count_total),
                StaffRegistry.name.asc(),
            )
        ).all()
        if args.limit:
            rows = rows[: args.limit]

        failures = 0
        for staff, profile, _paper_count, _missing_summaries in rows:
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
