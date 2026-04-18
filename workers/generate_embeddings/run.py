from __future__ import annotations

import argparse

from sqlalchemy import desc, select

from workers.common.db import worker_session
from workers.common.bootstrap import ensure_api_path
from workers.generate_embeddings.embed_papers import build_paper_embedding_text
from workers.generate_embeddings.embed_staff import build_staff_research_text, build_staff_summary_text


ensure_api_path()

from app.models.paper import Paper  # noqa: E402
from app.models.staff import StaffMatchProfile, StaffRegistry  # noqa: E402
from app.services.llm_client import embed_text, embed_texts  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate pgvector embeddings for staff profiles and papers.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of staff to process.")
    args = parser.parse_args()

    with worker_session() as session:
        rows = session.execute(
            select(StaffRegistry, StaffMatchProfile)
            .join(StaffMatchProfile, StaffRegistry.id == StaffMatchProfile.staff_id)
            .where(StaffRegistry.eligible_for_matching.is_(True))
            .order_by(
                desc(StaffMatchProfile.publication_count),
                desc(StaffMatchProfile.citation_count_total),
                StaffRegistry.name.asc(),
            )
        ).all()
        if args.limit:
            rows = rows[: args.limit]

        failures = 0
        for staff, profile in rows:
            try:
                with session.begin_nested():
                    papers = session.execute(
                        select(Paper).where(Paper.staff_id == staff.id).order_by(Paper.year.desc().nullslast())
                    ).scalars().all()
                    summary_embedding = embed_text(build_staff_summary_text(staff, profile))
                    research_embedding = embed_text(build_staff_research_text(profile, papers))
                    profile.embedding_summary = summary_embedding or None
                    profile.embedding_research = research_embedding or None
                    session.add(profile)

                    paper_texts = [build_paper_embedding_text(paper) for paper in papers]
                    paper_embeddings = embed_texts(paper_texts)
                    for paper, embedding in zip(papers, paper_embeddings):
                        paper.embedding_paper = embedding or None
                        session.add(paper)
                    session.flush()
            except Exception:
                failures += 1

    print(f"Generated embeddings for staff profiles and papers. Failures: {failures}.")


if __name__ == "__main__":
    main()
