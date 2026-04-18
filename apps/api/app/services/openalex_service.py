from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

import httpx

from app.core.config import settings


@dataclass
class OpenAlexAuthorCandidate:
    author_id: str
    display_name: str
    works_count: int
    cited_by_count: int
    last_known_institution: str | None
    raw: dict[str, Any]
    score: float


def build_openalex_client() -> httpx.Client:
    headers = {"User-Agent": "UtahResearchMatcher/0.1"}
    if settings.openalex_contact_email:
        headers["User-Agent"] = f"UtahResearchMatcher/0.1 ({settings.openalex_contact_email})"
    return httpx.Client(base_url=settings.openalex_base_url, timeout=30.0, headers=headers)


def search_authors(display_name: str, per_page: int = 10) -> list[dict[str, Any]]:
    with build_openalex_client() as client:
        response = client.get(
            "/authors",
            params=_params(
                {
                    "search": display_name,
                    "per-page": per_page,
                }
            ),
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("results", [])


def choose_best_author_match(
    *,
    display_name: str,
    email: str | None = None,
    department: str | None = None,
    school_affiliations: list[str] | None = None,
) -> OpenAlexAuthorCandidate | None:
    results = search_authors(display_name)
    if not results:
        return None

    candidates = []
    for item in results:
        score = _score_author_candidate(
            display_name=display_name,
            email=email,
            department=department,
            school_affiliations=school_affiliations or [],
            author=item,
        )
        candidate = OpenAlexAuthorCandidate(
            author_id=str(item.get("id") or "").replace("https://openalex.org/", ""),
            display_name=str(item.get("display_name") or ""),
            works_count=int(item.get("works_count") or 0),
            cited_by_count=int(item.get("cited_by_count") or 0),
            last_known_institution=_institution_name(item),
            raw=item,
            score=score,
        )
        candidates.append(candidate)

    candidates.sort(key=lambda candidate: (-candidate.score, -candidate.works_count, candidate.display_name))
    best = candidates[0]
    if best.score < 0.45:
        return None
    return best


def list_author_works(author_id: str, max_results: int | None = None) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    cursor = "*"
    with build_openalex_client() as client:
        while True:
            response = client.get(
                "/works",
                params=_params(
                    {
                        "filter": f"authorships.author.id:https://openalex.org/{author_id}",
                        "per-page": 200,
                        "cursor": cursor,
                    }
                ),
            )
            response.raise_for_status()
            payload = response.json()
            page_results = payload.get("results", [])
            results.extend(page_results)
            if max_results and len(results) >= max_results:
                return results[:max_results]
            cursor = payload.get("meta", {}).get("next_cursor")
            if not cursor or not page_results:
                break
    return results


def work_title(work: dict[str, Any]) -> str:
    return str(work.get("display_name") or "Untitled work").strip()


def work_abstract(work: dict[str, Any]) -> str | None:
    inverted_index = work.get("abstract_inverted_index")
    if not isinstance(inverted_index, dict):
        return None
    positions: dict[int, str] = {}
    for token, indexes in inverted_index.items():
        if not isinstance(indexes, list):
            continue
        for index in indexes:
            if isinstance(index, int):
                positions[index] = token
    if not positions:
        return None
    return " ".join(token for _index, token in sorted(positions.items()))


def work_paper_url(work: dict[str, Any]) -> str | None:
    primary_location = work.get("primary_location") or {}
    ids = work.get("ids") or {}
    return (
        primary_location.get("landing_page_url")
        or ids.get("doi")
        or ids.get("openalex")
    )


def work_pdf_url(work: dict[str, Any]) -> str | None:
    primary_location = work.get("primary_location") or {}
    open_access = work.get("open_access") or {}
    return primary_location.get("pdf_url") or open_access.get("oa_url")


def work_venue(work: dict[str, Any]) -> str | None:
    primary_location = work.get("primary_location") or {}
    source = primary_location.get("source") or {}
    return source.get("display_name")


def _params(values: dict[str, Any]) -> dict[str, Any]:
    params = dict(values)
    if settings.openalex_api_key:
        params["api_key"] = settings.openalex_api_key
    return params


def _score_author_candidate(
    *,
    display_name: str,
    email: str | None,
    department: str | None,
    school_affiliations: list[str],
    author: dict[str, Any],
) -> float:
    candidate_name = str(author.get("display_name") or "")
    institution = (_institution_name(author) or "").lower()
    score = SequenceMatcher(None, display_name.lower(), candidate_name.lower()).ratio() * 0.55

    if "utah" in institution:
        score += 0.25
    if email:
        email_local = email.split("@", 1)[0].lower()
        if email_local and email_local in candidate_name.lower().replace(" ", ""):
            score += 0.05
    if department and any(token in institution for token in department.lower().split()):
        score += 0.05
    if any(affiliation.lower().split()[0] in institution for affiliation in school_affiliations if affiliation):
        score += 0.05
    works_count = int(author.get("works_count") or 0)
    if works_count >= settings.minimum_publication_count:
        score += 0.05
    return min(score, 1.0)


def _institution_name(author: dict[str, Any]) -> str | None:
    institution = author.get("last_known_institutions") or []
    if isinstance(institution, list) and institution:
        return institution[0].get("display_name")
    return None

