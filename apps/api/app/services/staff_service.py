from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.models.paper import Paper, PaperAuthor
from app.models.staff import StaffMatchProfile, StaffRegistry
from app.schemas.paper import PaperListResponse, PaperSummary
from app.schemas.staff import (
    CollaboratorResponse,
    CollaboratorSummary,
    StaffBrowseItem,
    StaffBrowseResponse,
    StaffDetailResponse,
)


def get_staff_detail(db: Session, staff_id: str) -> StaffDetailResponse:
    row = db.execute(
        select(StaffRegistry, StaffMatchProfile)
        .join(StaffMatchProfile, StaffRegistry.id == StaffMatchProfile.staff_id, isouter=True)
        .where(StaffRegistry.id == staff_id)
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Staff member not found")

    staff, profile = row
    recent_papers = _paper_query(db, staff_id, sort="recent", limit=5, offset=0).items
    cited_papers = _paper_query(db, staff_id, sort="cited", limit=5, offset=0).items
    collaborators = _collaborator_query(db, staff_id)
    return StaffDetailResponse(
        staff_id=staff.id,
        name=staff.name,
        title=staff.title,
        email=staff.email,
        profile_url=staff.profile_url,
        image_url=staff.image_url,
        lab_url=staff.lab_url,
        primary_school=staff.primary_school,
        school_affiliations=staff.school_affiliations or [],
        department=staff.department,
        bio=staff.bio,
        ai_research_summary=profile.ai_research_summary if profile else (staff.bio or "Research summary not available yet."),
        recent_papers=recent_papers,
        most_cited_papers=cited_papers,
        searchable_papers_count=_paper_count(db, staff_id),
        key_outreach_points=_detail_outreach_points(staff, profile),
        collaborators=collaborators,
    )


def get_staff_papers(
    db: Session,
    staff_id: str,
    search: str | None,
    sort: str,
    limit: int,
    offset: int,
) -> PaperListResponse:
    return _paper_query(db, staff_id=staff_id, search=search, sort=sort, limit=limit, offset=offset)


def browse_staff(
    db: Session,
    *,
    search: str | None,
    school: str | None,
    department: str | None,
    eligible_only: bool,
    sort: str,
    limit: int,
    offset: int,
) -> StaffBrowseResponse:
    stmt = (
        select(StaffRegistry, StaffMatchProfile)
        .join(StaffMatchProfile, StaffRegistry.id == StaffMatchProfile.staff_id, isouter=True)
    )
    available_schools = _available_schools(db)

    if eligible_only:
        stmt = stmt.where(StaffRegistry.eligible_for_matching.is_(True))
    if school:
        stmt = stmt.where(StaffRegistry.primary_school == school)
    if department:
        query = f"%{department}%"
        stmt = stmt.where(StaffRegistry.department.ilike(query))
    if search:
        query = f"%{search}%"
        stmt = stmt.where(
            or_(
                StaffRegistry.name.ilike(query),
                StaffRegistry.department.ilike(query),
                StaffRegistry.primary_school.ilike(query),
                StaffRegistry.bio.ilike(query),
                StaffMatchProfile.ai_research_summary.ilike(query),
            )
        )

    if sort == "citations":
        stmt = stmt.order_by(
            desc(StaffRegistry.eligible_for_matching),
            desc(StaffMatchProfile.citation_count_total),
            desc(StaffMatchProfile.publication_count),
            StaffRegistry.name.asc(),
        )
    elif sort == "papers":
        stmt = stmt.order_by(
            desc(StaffRegistry.eligible_for_matching),
            desc(StaffMatchProfile.publication_count),
            desc(StaffMatchProfile.citation_count_total),
            StaffRegistry.name.asc(),
        )
    elif sort == "recent":
        stmt = stmt.order_by(
            desc(StaffRegistry.eligible_for_matching),
            desc(StaffMatchProfile.last_active_year),
            desc(StaffMatchProfile.publication_count),
            StaffRegistry.name.asc(),
        )
    else:
        stmt = stmt.order_by(
            desc(StaffRegistry.eligible_for_matching),
            StaffRegistry.name.asc(),
        )

    total_stmt = (
        select(func.count(StaffRegistry.id))
        .join(StaffMatchProfile, StaffRegistry.id == StaffMatchProfile.staff_id, isouter=True)
    )
    if eligible_only:
        total_stmt = total_stmt.where(StaffRegistry.eligible_for_matching.is_(True))
    if school:
        total_stmt = total_stmt.where(StaffRegistry.primary_school == school)
    if department:
        query = f"%{department}%"
        total_stmt = total_stmt.where(StaffRegistry.department.ilike(query))
    if search:
        query = f"%{search}%"
        total_stmt = total_stmt.where(
            or_(
                StaffRegistry.name.ilike(query),
                StaffRegistry.department.ilike(query),
                StaffRegistry.primary_school.ilike(query),
                StaffRegistry.bio.ilike(query),
                StaffMatchProfile.ai_research_summary.ilike(query),
            )
        )

    total = int(db.execute(total_stmt).scalar_one())
    rows = db.execute(stmt.offset(offset).limit(limit)).all()
    items = [_to_staff_browse_item(staff, profile) for staff, profile in rows]
    return StaffBrowseResponse(total=total, available_schools=available_schools, items=items)


def get_staff_collaborators(db: Session, staff_id: str) -> CollaboratorResponse:
    return CollaboratorResponse(staff_id=staff_id, collaborators=_collaborator_query(db, staff_id))


def _paper_query(
    db: Session,
    staff_id: str,
    search: str | None = None,
    sort: str = "recent",
    limit: int = 25,
    offset: int = 0,
) -> PaperListResponse:
    stmt = select(Paper).where(Paper.staff_id == staff_id)
    if search:
        query = f"%{search}%"
        stmt = stmt.where(or_(Paper.title.ilike(query), Paper.abstract.ilike(query), Paper.ai_summary.ilike(query)))

    if sort == "cited":
        stmt = stmt.order_by(desc(Paper.is_top_cited), desc(Paper.citation_count), desc(Paper.year))
    else:
        stmt = stmt.order_by(desc(Paper.is_recent), desc(Paper.year), desc(Paper.citation_count))

    total = _paper_count(db, staff_id, search)
    papers = db.execute(stmt.offset(offset).limit(limit)).scalars().all()
    return PaperListResponse(
        staff_id=staff_id,
        total=total,
        items=[
            PaperSummary(
                id=paper.id,
                title=paper.title,
                year=paper.year,
                venue=paper.venue,
                citation_count=paper.citation_count,
                paper_url=paper.paper_url,
                pdf_url=paper.pdf_url,
                ai_summary=paper.ai_summary,
            )
            for paper in papers
        ],
    )


def _paper_count(db: Session, staff_id: str, search: str | None = None) -> int:
    stmt = select(func.count(Paper.id)).where(Paper.staff_id == staff_id)
    if search:
        query = f"%{search}%"
        stmt = stmt.where(or_(Paper.title.ilike(query), Paper.abstract.ilike(query), Paper.ai_summary.ilike(query)))
    return int(db.execute(stmt).scalar_one())


def _collaborator_query(db: Session, staff_id: str) -> list[CollaboratorSummary]:
    rows = db.execute(
        select(
            PaperAuthor.author_name,
            PaperAuthor.affiliation,
            PaperAuthor.is_uofu,
            PaperAuthor.profile_url,
            Paper.title,
            PaperAuthor.matched_staff_id,
        )
        .join(Paper, Paper.id == PaperAuthor.paper_id)
        .where(Paper.staff_id == staff_id)
        .order_by(PaperAuthor.is_uofu.desc(), PaperAuthor.author_name.asc())
    ).all()
    grouped: dict[tuple[str, str | None, bool, str | None], list[str]] = {}
    collaborators = []
    for name, affiliation, is_uofu, profile_url, paper_title, matched_staff_id in rows:
        if matched_staff_id == staff_id:
            continue
        key = (name, affiliation, bool(is_uofu), profile_url)
        grouped.setdefault(key, [])
        if paper_title and paper_title not in grouped[key]:
            grouped[key].append(paper_title)

    ordered_keys = sorted(grouped.keys(), key=lambda item: (not item[2], item[0]))
    for name, affiliation, is_uofu, profile_url in ordered_keys:
        collaborators.append(
            CollaboratorSummary(
                name=name,
                affiliation=affiliation,
                is_uofu=bool(is_uofu),
                profile_url=profile_url,
                related_papers=grouped[(name, affiliation, is_uofu, profile_url)][:3],
            )
        )
    return collaborators[:12]


def _detail_outreach_points(staff: StaffRegistry, profile: StaffMatchProfile | None) -> list[str]:
    points = [
        f"Open with a specific question about how {staff.name}'s research connects to the company's sector.",
        "Reference one recent paper and one historically influential paper to show you reviewed their work.",
    ]
    if profile and profile.technical_tags:
        points.append(f"Mention overlap in {', '.join(profile.technical_tags[:3])}.")
    return points


def _available_schools(db: Session) -> list[str]:
    rows = db.execute(
        select(StaffRegistry.primary_school)
        .where(StaffRegistry.primary_school.is_not(None))
        .distinct()
        .order_by(StaffRegistry.primary_school.asc())
    ).scalars().all()
    return [school for school in rows if school]


def _to_staff_browse_item(staff: StaffRegistry, profile: StaffMatchProfile | None) -> StaffBrowseItem:
    return StaffBrowseItem(
        staff_id=staff.id,
        name=staff.name,
        title=staff.title,
        profile_url=staff.profile_url,
        image_url=staff.image_url,
        lab_url=staff.lab_url,
        primary_school=staff.primary_school,
        school_affiliations=staff.school_affiliations or [],
        department=staff.department,
        ai_research_summary=profile.ai_research_summary if profile else (staff.bio or "Research summary not available yet."),
        publication_count=profile.publication_count if profile and profile.publication_count else 0,
        citation_count_total=profile.citation_count_total if profile and profile.citation_count_total else 0,
        last_active_year=profile.last_active_year if profile else None,
        eligible_for_matching=staff.eligible_for_matching,
        has_publication_signal=staff.has_publication_signal,
    )
