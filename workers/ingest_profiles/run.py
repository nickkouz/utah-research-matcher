from __future__ import annotations

import argparse

from workers.common.db import worker_session
from workers.ingest_profiles.parser import parse_profile_html
from workers.ingest_profiles.repository import upsert_staff_profiles
from workers.ingest_profiles.scraper import fetch_profile_pages


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest public Utah faculty profiles into staff_registry.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of profile pages to ingest.")
    args = parser.parse_args()

    pages = fetch_profile_pages(limit=args.limit)
    profiles = []
    for profile_url, html in pages:
        parsed = parse_profile_html(html, profile_url)
        if parsed:
            profiles.append(parsed)

    with worker_session() as session:
        inserted = upsert_staff_profiles(session, profiles)
    print(f"Ingested {inserted} profiles into staff_registry.")


if __name__ == "__main__":
    main()

