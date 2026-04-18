from __future__ import annotations

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.staff import StaffRegistry
from workers.ingest_profiles.parser import ParsedStaffProfile


def upsert_staff_profiles(session: Session, profiles: list[ParsedStaffProfile]) -> int:
    if not profiles:
        return 0
    values = [
        {
            "id": profile.id,
            "profile_slug": profile.profile_slug,
            "name": profile.name,
            "title": profile.title,
            "email": profile.email,
            "profile_url": profile.profile_url,
            "image_url": profile.image_url,
            "lab_url": profile.lab_url,
            "bio": profile.bio,
            "primary_school": profile.primary_school,
            "school_affiliations": profile.school_affiliations,
            "department": profile.department,
            "source_system": "profiles.faculty.utah.edu",
        }
        for profile in profiles
    ]
    stmt = insert(StaffRegistry).values(values)
    stmt = stmt.on_conflict_do_update(
        index_elements=[StaffRegistry.id],
        set_={
            "profile_slug": stmt.excluded.profile_slug,
            "name": stmt.excluded.name,
            "title": stmt.excluded.title,
            "email": stmt.excluded.email,
            "profile_url": stmt.excluded.profile_url,
            "image_url": stmt.excluded.image_url,
            "lab_url": stmt.excluded.lab_url,
            "bio": stmt.excluded.bio,
            "primary_school": stmt.excluded.primary_school,
            "school_affiliations": stmt.excluded.school_affiliations,
            "department": stmt.excluded.department,
            "source_system": stmt.excluded.source_system,
        },
    )
    session.execute(stmt)
    return len(values)
