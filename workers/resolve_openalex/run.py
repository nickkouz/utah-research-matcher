from __future__ import annotations

import argparse

from sqlalchemy import select

from workers.common.db import worker_session
from workers.resolve_openalex.repository import upsert_author_match
from workers.common.bootstrap import ensure_api_path


ensure_api_path()

from app.models.staff import StaffRegistry  # noqa: E402
from app.services.openalex_service import choose_best_author_match  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve Utah staff to OpenAlex authors.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of staff to process.")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Re-run resolution even for staff who already have an OpenAlex author ID.",
    )
    args = parser.parse_args()

    with worker_session() as session:
        stmt = select(StaffRegistry).order_by(StaffRegistry.name.asc())
        staff_rows = session.execute(stmt).scalars().all()
        if not args.refresh:
            staff_rows = [
                staff
                for staff in staff_rows
                if not staff.match_profile or not staff.match_profile.openalex_author_id
            ]
        if args.limit:
            staff_rows = staff_rows[: args.limit]

        matched = 0
        failures = 0
        for staff in staff_rows:
            try:
                best = choose_best_author_match(
                    display_name=staff.name,
                    email=staff.email,
                    department=staff.department,
                    school_affiliations=staff.school_affiliations,
                )
                if not best:
                    continue
                upsert_author_match(session, staff=staff, author=best)
                matched += 1
            except Exception:
                failures += 1

    print(f"Resolved {matched} staff profiles to OpenAlex authors. Failures: {failures}.")


if __name__ == "__main__":
    main()
