from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.paper import Paper, PaperAuthor
from app.models.staff import StaffMatchProfile, StaffRegistry
from app.schemas.diagnostics import DiagnosticsSummary, NamedCount


router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])


@router.get("/summary", response_model=DiagnosticsSummary)
def diagnostics_summary(db: Session = Depends(get_db)) -> DiagnosticsSummary:
    counts = {
        "staff_registry": int(db.execute(select(func.count(StaffRegistry.id))).scalar_one()),
        "staff_match_profiles": int(db.execute(select(func.count(StaffMatchProfile.staff_id))).scalar_one()),
        "eligible_staff": int(
            db.execute(
                select(func.count(StaffRegistry.id)).where(StaffRegistry.eligible_for_matching.is_(True))
            ).scalar_one()
        ),
        "papers": int(db.execute(select(func.count(Paper.id))).scalar_one()),
        "paper_authors": int(db.execute(select(func.count(PaperAuthor.id))).scalar_one()),
    }

    total_by_school_rows = db.execute(
        select(StaffRegistry.primary_school, func.count(StaffRegistry.id))
        .group_by(StaffRegistry.primary_school)
        .order_by(func.count(StaffRegistry.id).desc())
        .limit(10)
    ).all()
    eligible_by_school_rows = db.execute(
        select(StaffRegistry.primary_school, func.count(StaffRegistry.id))
        .where(StaffRegistry.eligible_for_matching.is_(True))
        .group_by(StaffRegistry.primary_school)
        .order_by(func.count(StaffRegistry.id).desc())
        .limit(10)
    ).all()
    generic_eligible_profiles = int(
        db.execute(
            select(func.count(StaffMatchProfile.staff_id))
            .join(StaffRegistry, StaffRegistry.id == StaffMatchProfile.staff_id)
            .where(StaffRegistry.eligible_for_matching.is_(True))
            .where(
                or_(
                    StaffMatchProfile.ai_research_summary.ilike("%biography and contact information%"),
                    StaffMatchProfile.ai_research_summary.ilike("%contact information for%"),
                    StaffMatchProfile.ai_research_summary.ilike("%learn more at%"),
                )
            )
        ).scalar_one()
    )

    return DiagnosticsSummary(
        counts=counts,
        total_by_school=[_named_count(name, count) for name, count in total_by_school_rows],
        eligible_by_school=[_named_count(name, count) for name, count in eligible_by_school_rows],
        generic_eligible_profiles=generic_eligible_profiles,
    )


def _named_count(name: str | None, count: int) -> NamedCount:
    return NamedCount(name=name or "Unspecified", count=int(count))
