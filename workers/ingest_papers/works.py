from __future__ import annotations

from datetime import datetime

from app.models.staff import StaffMatchProfile, StaffRegistry
from app.services.openalex_service import (
    list_author_works,
    work_abstract,
    work_paper_url,
    work_pdf_url,
    work_title,
    work_venue,
)


def build_paper_records(
    *,
    staff: StaffRegistry,
    profile: StaffMatchProfile,
    works: list[dict],
) -> list[dict]:
    current_year = datetime.now().year
    sorted_by_year = sorted(
        works,
        key=lambda work: (work.get("publication_year") or 0, work.get("cited_by_count") or 0),
        reverse=True,
    )
    sorted_by_citations = sorted(
        works,
        key=lambda work: (work.get("cited_by_count") or 0, work.get("publication_year") or 0),
        reverse=True,
    )
    recent_ids = {str(work.get("id") or "").replace("https://openalex.org/", "") for work in sorted_by_year[:5]}
    cited_ids = {str(work.get("id") or "").replace("https://openalex.org/", "") for work in sorted_by_citations[:5]}

    records = []
    for work in works:
        work_id = str(work.get("id") or "").replace("https://openalex.org/", "")
        year = work.get("publication_year")
        records.append(
            {
                "id": f"{staff.id}::{work_id}",
                "staff_id": staff.id,
                "openalex_work_id": work_id,
                "title": work_title(work),
                "year": int(year) if year else None,
                "venue": work_venue(work),
                "abstract": work_abstract(work),
                "paper_url": work_paper_url(work),
                "pdf_url": work_pdf_url(work),
                "citation_count": int(work.get("cited_by_count") or 0),
                "is_recent": bool(year and int(year) >= current_year - 2) or work_id in recent_ids,
                "is_top_cited": work_id in cited_ids,
            }
        )
    return records
