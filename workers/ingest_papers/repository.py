from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.paper import Paper, PaperAuthor


def upsert_papers(session: Session, paper_values: list[dict]) -> None:
    if not paper_values:
        return
    stmt = insert(Paper).values(paper_values)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Paper.id],
        set_={
            "staff_id": stmt.excluded.staff_id,
            "openalex_work_id": stmt.excluded.openalex_work_id,
            "title": stmt.excluded.title,
            "year": stmt.excluded.year,
            "venue": stmt.excluded.venue,
            "abstract": stmt.excluded.abstract,
            "paper_url": stmt.excluded.paper_url,
            "pdf_url": stmt.excluded.pdf_url,
            "citation_count": stmt.excluded.citation_count,
            "is_recent": stmt.excluded.is_recent,
            "is_top_cited": stmt.excluded.is_top_cited,
        },
    )
    session.execute(stmt)


def replace_paper_authors(session: Session, paper_id: str, authors: list[PaperAuthor]) -> None:
    session.execute(delete(PaperAuthor).where(PaperAuthor.paper_id == paper_id))
    for author in authors:
        session.add(author)

