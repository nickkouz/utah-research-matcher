from __future__ import annotations

import math
from collections import Counter
from datetime import datetime
import re

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.paper import Paper, PaperAuthor
from app.models.staff import StaffMatchProfile, StaffRegistry
from app.schemas.company import CompanyInterpretation
from app.schemas.paper import PaperSummary
from app.schemas.staff import CollaboratorSummary, StaffSummaryResponse
from app.services.embedding_service import company_query_embeddings
from app.services.rerank_service import rerank_candidates

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z\\-]+")
GENERIC_PROFILE_PHRASES = (
    "biography and contact information",
    "contact information for",
    "learn more at",
)


def match_company_to_staff(
    db: Session,
    company: CompanyInterpretation,
    limit: int = 8,
) -> list[StaffSummaryResponse]:
    summary_embedding, theme_embedding = company_query_embeddings(company)
    rows = _candidate_rows(db=db, limit=limit)

    candidates: list[StaffSummaryResponse] = []
    for staff, profile, is_primary_candidate in rows:
        score = _score_candidate(
            company,
            summary_embedding,
            theme_embedding,
            staff,
            profile,
            is_primary_candidate=is_primary_candidate,
        )
        candidates.append(
            StaffSummaryResponse(
                staff_id=staff.id,
                name=staff.name,
                title=staff.title,
                image_url=staff.image_url,
                lab_url=staff.lab_url,
                primary_school=staff.primary_school,
                school_affiliations=staff.school_affiliations or [],
                department=staff.department,
                ai_research_summary=profile.ai_research_summary,
                match_reason=_match_reason(company, staff, profile),
                score=round(score, 4),
                recent_papers=_paper_summaries(db, staff.id, recent=True),
                most_cited_papers=_paper_summaries(db, staff.id, cited=True),
                key_outreach_points=_outreach_points(company, staff, profile),
                further_contacts=_collaborators(db, staff.id),
            )
        )

    candidates.sort(key=lambda item: item.score, reverse=True)
    reranked = rerank_candidates(company, candidates[:20])
    return reranked[:limit]


def _candidate_rows(
    db: Session,
    limit: int,
) -> list[tuple[StaffRegistry, StaffMatchProfile, bool]]:
    stmt = (
        select(StaffRegistry, StaffMatchProfile)
        .join(StaffMatchProfile, StaffRegistry.id == StaffMatchProfile.staff_id)
        .order_by(
            desc(StaffRegistry.eligible_for_matching),
            desc(StaffRegistry.has_publication_signal),
            desc(StaffMatchProfile.publication_count),
            desc(StaffMatchProfile.citation_count_total),
            StaffRegistry.name.asc(),
        )
    )
    rows = db.execute(stmt).all()
    primary_rows = [
        (staff, profile, True)
        for staff, profile in rows
        if staff.eligible_for_matching
    ]
    if len(primary_rows) >= max(limit, 5):
        return primary_rows

    fallback_rows = [
        (staff, profile, False)
        for staff, profile in rows
        if (not staff.eligible_for_matching)
        and (
            staff.has_publication_signal
            or (profile.publication_count or 0) > 0
            or bool(profile.last_active_year)
        )
    ]
    combined = primary_rows + fallback_rows
    return combined[: max(limit * 4, 20)]


def _score_candidate(
    company: CompanyInterpretation,
    summary_embedding: list[float],
    theme_embedding: list[float],
    staff: StaffRegistry,
    profile: StaffMatchProfile,
    *,
    is_primary_candidate: bool,
) -> float:
    company_summary_text = company.research_need_summary
    company_theme_text = _company_theme_text(company)
    profile_summary_text = profile.ai_research_summary
    profile_research_text = _profile_research_text(profile)

    summary_similarity = _semantic_similarity(
        summary_embedding,
        _vector_values(profile.embedding_summary),
        company_summary_text,
        profile_summary_text,
    )
    research_similarity = _semantic_similarity(
        theme_embedding,
        _vector_values(profile.embedding_research),
        company_theme_text,
        profile_research_text,
    )
    sector_overlap = _overlap(company.primary_sector, profile.sector_tags or [])
    theme_overlap = _multi_overlap(company.technical_themes, profile.technical_tags or [])
    recency = _recency(profile.last_active_year)
    school_support = _multi_overlap(company.school_affinities, staff.school_affiliations or [])
    publication_support = _publication_support(profile)
    eligibility_support = 1.0 if is_primary_candidate else 0.65
    profile_quality = _profile_quality(profile)
    return (
        (summary_similarity * 0.40)
        + (research_similarity * 0.25)
        + (sector_overlap * 0.12)
        + (theme_overlap * 0.08)
        + (recency * 0.05)
        + (school_support * 0.03)
        + (publication_support * 0.04)
        + (eligibility_support * 0.03)
        + (profile_quality * 0.03)
    )


def _paper_summaries(db: Session, staff_id: str, recent: bool = False, cited: bool = False) -> list[PaperSummary]:
    stmt = select(Paper).where(Paper.staff_id == staff_id)
    if recent:
        stmt = stmt.order_by(Paper.is_recent.desc(), Paper.year.desc().nullslast(), Paper.citation_count.desc())
    elif cited:
        stmt = stmt.order_by(Paper.is_top_cited.desc(), Paper.citation_count.desc(), Paper.year.desc().nullslast())
    else:
        stmt = stmt.order_by(Paper.year.desc().nullslast())
    papers = db.execute(stmt.limit(3)).scalars().all()
    return [_to_paper_summary(paper) for paper in papers]


def _company_theme_text(company: CompanyInterpretation) -> str:
    return " ".join(
        filter(
            None,
            [
                company.primary_sector,
                company.subsector or "",
                " ".join(company.technical_themes),
                " ".join(company.market_keywords),
            ],
        )
    )


def _profile_research_text(profile: StaffMatchProfile) -> str:
    return " ".join(
        filter(
            None,
            [
                profile.ai_research_summary,
                " ".join(profile.research_keywords or []),
                " ".join(profile.technical_tags or []),
                " ".join(profile.sector_tags or []),
            ],
        )
    )


def _publication_support(profile: StaffMatchProfile) -> float:
    publication_count = profile.publication_count or 0
    citation_count = profile.citation_count_total or 0
    publication_score = min(publication_count / max(settings.minimum_publication_count * 4, 1), 1.0)
    citation_score = min(citation_count / 250.0, 1.0)
    return (publication_score * 0.6) + (citation_score * 0.4)


def _profile_quality(profile: StaffMatchProfile) -> float:
    summary = (profile.ai_research_summary or "").strip().lower()
    if not summary:
        return 0.0
    if any(phrase in summary for phrase in GENERIC_PROFILE_PHRASES):
        return 0.1
    word_count = len(summary.split())
    if word_count < 12:
        return 0.3
    return 1.0


def _collaborators(db: Session, staff_id: str) -> list[CollaboratorSummary]:
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
    ).all()
    if not rows:
        return []

    aggregated: dict[tuple[str, str | None, bool, str | None], list[str]] = {}
    counts = Counter()
    for name, affiliation, is_uofu, profile_url, paper_title, matched_staff_id in rows:
        if matched_staff_id == staff_id:
            continue
        key = (name, affiliation, bool(is_uofu), profile_url)
        counts[key] += 1
        aggregated.setdefault(key, [])
        if paper_title and paper_title not in aggregated[key]:
            aggregated[key].append(paper_title)
    ordered = sorted(counts.items(), key=lambda item: (not item[0][2], -item[1], item[0][0]))
    collaborators = []
    for (name, affiliation, is_uofu, profile_url), _count in ordered[:5]:
        collaborators.append(
            CollaboratorSummary(
                name=name,
                affiliation=affiliation,
                is_uofu=bool(is_uofu),
                profile_url=profile_url,
                related_papers=aggregated[(name, affiliation, is_uofu, profile_url)][:3],
            )
        )
    return collaborators


def _match_reason(company: CompanyInterpretation, staff: StaffRegistry, profile: StaffMatchProfile) -> str:
    school_text = ", ".join(staff.school_affiliations or ([staff.primary_school] if staff.primary_school else []))
    leading_tags = (profile.technical_tags or [])[:3] or (profile.research_keywords or [])[:3]
    return (
        f"{staff.name} is relevant for {company.company_name} because their research aligns with "
        f"{company.primary_sector.lower()} themes such as {', '.join(leading_tags) or 'adjacent technical work'}. "
        f"They are affiliated with {school_text or 'the University of Utah'} and have recent research activity in this area."
    )


def _outreach_points(
    company: CompanyInterpretation,
    staff: StaffRegistry,
    profile: StaffMatchProfile,
) -> list[str]:
    tags = (profile.technical_tags or [])[:3]
    points = [
        f"Mention {company.company_name}'s work in {company.primary_sector.lower()} and ask how it overlaps with {staff.name}'s research.",
        f"Reference themes like {', '.join(tags) or 'their recent research topics'} when starting the conversation.",
    ]
    if profile.last_active_year:
        points.append(f"Point to their recent publication activity through {profile.last_active_year}.")
    return points


def _to_paper_summary(paper: Paper) -> PaperSummary:
    return PaperSummary(
        id=paper.id,
        title=paper.title,
        year=paper.year,
        venue=paper.venue,
        citation_count=paper.citation_count,
        paper_url=paper.paper_url,
        pdf_url=paper.pdf_url,
        ai_summary=paper.ai_summary,
    )


def _semantic_similarity(
    left_embedding: list[float],
    right_embedding: list[float],
    left_text: str,
    right_text: str,
) -> float:
    vector_score = _cosine(left_embedding, right_embedding)
    if vector_score > 0:
        return vector_score
    return _jaccard(left_text, right_text)


def _vector_values(value: object | None) -> list[float]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        converted = tolist()
        if isinstance(converted, list):
            return converted
        return list(converted)
    return list(value)


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return max(numerator / (left_norm * right_norm), 0.0)


def _jaccard(left_text: str, right_text: str) -> float:
    left_tokens = {token.lower() for token in TOKEN_RE.findall(left_text)}
    right_tokens = {token.lower() for token in TOKEN_RE.findall(right_text)}
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _overlap(value: str, items: list[str]) -> float:
    lowered = value.strip().lower()
    if not lowered or not items:
        return 0.0
    normalized = {item.lower() for item in items}
    if lowered in normalized:
        return 1.0
    if any(lowered in item or item in lowered for item in normalized):
        return 0.6
    return 0.0


def _multi_overlap(left: list[str], right: list[str]) -> float:
    if not left or not right:
        return 0.0
    left_norm = {item.strip().lower() for item in left if item.strip()}
    right_norm = {item.strip().lower() for item in right if item.strip()}
    if not left_norm or not right_norm:
        return 0.0
    exact = left_norm & right_norm
    fuzzy = {
        left_item
        for left_item in left_norm
        for right_item in right_norm
        if left_item in right_item or right_item in left_item
    }
    return len(exact | fuzzy) / len(left_norm | right_norm)


def _recency(last_active_year: int | None) -> float:
    if not last_active_year:
        return 0.2
    delta = datetime.now().year - last_active_year
    if delta <= 1:
        return 1.0
    if delta == 2:
        return 0.8
    if delta == 3:
        return 0.5
    return 0.2
