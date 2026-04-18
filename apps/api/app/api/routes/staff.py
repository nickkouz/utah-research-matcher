from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.paper import PaperListResponse
from app.schemas.staff import CollaboratorResponse, StaffBrowseResponse, StaffDetailResponse
from app.services.staff_service import browse_staff, get_staff_collaborators, get_staff_detail, get_staff_papers


router = APIRouter(prefix="/staff", tags=["staff"])


@router.get("", response_model=StaffBrowseResponse)
def staff_browse(
    search: str | None = Query(default=None),
    school: str | None = Query(default=None),
    department: str | None = Query(default=None),
    eligible_only: bool = Query(default=False),
    sort: str = Query(default="papers"),
    limit: int = Query(default=48, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> StaffBrowseResponse:
    return browse_staff(
        db=db,
        search=search,
        school=school,
        department=department,
        eligible_only=eligible_only,
        sort=sort,
        limit=limit,
        offset=offset,
    )


@router.get("/{staff_id}", response_model=StaffDetailResponse)
def staff_detail(staff_id: str, db: Session = Depends(get_db)) -> StaffDetailResponse:
    return get_staff_detail(db=db, staff_id=staff_id)


@router.get("/{staff_id}/papers", response_model=PaperListResponse)
def staff_papers(
    staff_id: str,
    search: str | None = Query(default=None),
    sort: str = Query(default="recent"),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> PaperListResponse:
    return get_staff_papers(
        db=db,
        staff_id=staff_id,
        search=search,
        sort=sort,
        limit=limit,
        offset=offset,
    )


@router.get("/{staff_id}/collaborators", response_model=CollaboratorResponse)
def staff_collaborators(staff_id: str, db: Session = Depends(get_db)) -> CollaboratorResponse:
    return get_staff_collaborators(db=db, staff_id=staff_id)
