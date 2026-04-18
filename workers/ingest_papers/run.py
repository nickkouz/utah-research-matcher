from __future__ import annotations

import argparse

from sqlalchemy import case, desc, func, select

from workers.common.db import worker_session
from workers.common.bootstrap import ensure_api_path
from workers.ingest_papers.authorships import authors_from_work
from workers.ingest_papers.repository import replace_paper_authors, upsert_papers
from workers.ingest_papers.works import build_paper_records


ensure_api_path()

from app.models.staff import StaffMatchProfile, StaffRegistry  # noqa: E402
from app.services.openalex_service import list_author_works  # noqa: E402

def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest OpenAlex works into papers and paper_authors.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of staff to process.")
    parser.add_argument(
        "--staff-id",
        type=str,
        default=None,
        help="Restrict ingest to a single staff ID for debugging.",
    )
    args = parser.parse_args()

    with worker_session() as session:
        paper_counts = (
            select(Paper.staff_id.label("staff_id"), func.count(Paper.id).label("paper_count"))
            .group_by(Paper.staff_id)
            .subquery()
        )
        stmt = (
            select(StaffRegistry, StaffMatchProfile, paper_counts.c.paper_count)
            .join(StaffMatchProfile, StaffRegistry.id == StaffMatchProfile.staff_id)
            .outerjoin(paper_counts, paper_counts.c.staff_id == StaffRegistry.id)
            .where(StaffMatchProfile.openalex_author_id.is_not(None))
            .order_by(
                desc(case((paper_counts.c.paper_count.is_(None), 1), else_=0)),
                desc(StaffRegistry.eligible_for_matching),
                paper_counts.c.paper_count.asc().nullslast(),
                desc(StaffMatchProfile.publication_count),
                desc(StaffMatchProfile.citation_count_total),
                StaffRegistry.name.asc(),
            )
        )
        if args.staff_id:
            stmt = stmt.where(StaffRegistry.id == args.staff_id)
        rows = session.execute(stmt).all()
        if args.limit:
            rows = rows[: args.limit]
        known_staff = session.execute(select(StaffRegistry)).scalars().all()

        total_papers = 0
        failures = 0
        for staff, profile, _existing_paper_count in rows:
            try:
                works = list_author_works(profile.openalex_author_id or "")
                paper_records = build_paper_records(staff=staff, profile=profile, works=works)
                upsert_papers(session, paper_records)
                total_papers += len(paper_records)

                paper_id_map = {
                    str(work.get("id") or "").replace("https://openalex.org/", ""): f"{staff.id}::{str(work.get('id') or '').replace('https://openalex.org/', '')}"
                    for work in works
                }
                for work in works:
                    work_id = str(work.get("id") or "").replace("https://openalex.org/", "")
                    local_paper_id = paper_id_map.get(work_id)
                    if not local_paper_id:
                        continue
                    authors = authors_from_work(paper_id=local_paper_id, work=work, known_staff=known_staff)
                    replace_paper_authors(session, local_paper_id, authors)
            except Exception:
                failures += 1

    print(f"Ingested or updated {total_papers} papers. Failures: {failures}.")


if __name__ == "__main__":
    main()
