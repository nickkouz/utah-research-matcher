from __future__ import annotations

from collections.abc import Iterable

from app.models.paper import PaperAuthor
from app.models.staff import StaffRegistry
from workers.common.text import normalize_name


def authors_from_work(
    *,
    paper_id: str,
    work: dict,
    known_staff: Iterable[StaffRegistry],
) -> list[PaperAuthor]:
    known_by_name = {normalize_name(staff.name).lower(): staff for staff in known_staff}
    authorships = work.get("authorships") or []
    authors: list[PaperAuthor] = []
    for index, authorship in enumerate(authorships, start=1):
        author = authorship.get("author") or {}
        author_name = str(author.get("display_name") or "").strip()
        if not author_name:
            continue
        institutions = authorship.get("institutions") or []
        affiliation_names = [item.get("display_name") for item in institutions if item.get("display_name")]
        affiliation = "; ".join(affiliation_names) if affiliation_names else None
        is_uofu = any("utah" in name.lower() for name in affiliation_names)
        normalized = normalize_name(author_name).lower()
        matched_staff = known_by_name.get(normalized)
        authors.append(
            PaperAuthor(
                paper_id=paper_id,
                author_name=author_name,
                author_position=index,
                is_uofu=is_uofu,
                matched_staff_id=matched_staff.id if matched_staff else None,
                affiliation=affiliation,
                profile_url=matched_staff.profile_url if matched_staff else None,
            )
        )
    return authors

