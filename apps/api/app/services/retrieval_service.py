from __future__ import annotations

import math
from collections import Counter
from datetime import datetime
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.paper import Paper, PaperAuthor
from app.models.staff import StaffMatchProfile, StaffRegistry
from app.schemas.company import CompanyInterpretation
from app.schemas.paper import PaperSummary
from app.schemas.staff import CollaboratorSummary, StaffSummaryResponse
from app.services.embedding_service import company_query_embeddings
from app.services.rerank_service import rerank_candidates

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z\\-]+")


def match_company_to_staff(
    db: Session,
    company: CompanyInterpretation,
    limit: int = 8,
) -> list[StaffSummaryResponse]:
    summary_embedding, theme_embedding = company_query_embeddings(company)
    rows = db.execute(
        select(StaffRegistry, StaffMatchProfile)
        .join(StaffMatchProfile, StaffRegistry.id == StaffMatchProfile.staff_id)
        .where(StaffRegistry.eligible_for_matching.is_(True))
    ).all()

    candidates: list[StaffSummaryResponse] = []
    for staff, profile in rows:
        score = _score_candidate(company, summary_embedding, theme_embedding, staff, profile)
        candidates.append(
            StaffSummaryResponse(
                staff_id=staff.id,
                name=staff.name,
                title=staff.title,
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


def _score_candidate(
    company: CompanyInterpretation,
    summary_embedding: list[float],
    theme_embedding: list[float],
    staff: StaffRegistry,
    profile: StaffMatchProfile,
) -> float:
    company_summary_text = company.research_need_summary
    company_theme_text = _company_theme_text(company)
    profile_summary_text = profile.ai_research_summary
    profile_research_text = _profile_research_text(profile)

    summary_similarity = _semantic_similarity(
        summary_embedding,
        profile.embedding_summary or [],
        company_summary_text,
        profile_summary_text,
    )
    research_similarity = _semantic_similarity(
        theme_embedding,
        profile.embedding_research or [],
        company_theme_text,
        profile_research_text,
    )
    sector_overlap = _overlap(company.primary_sector, profile.sector_tags or [])
    theme_overlap = _multi_overlap(company.technical_themes, profile.technical_tags or [])
    recency = _recency(profile.last_active_year)
    school_support = _multi_overlap(company.school_affinities, staff.school_affiliations or [])
    return (
        (summary_similarity * 0.45)
        + (research_similarity * 0.25)
        + (sector_overlap * 0.15)
        + (theme_overlap * 0.10)
        + (recency * 0.05)
        + (school_support * 0.05)
    )


def _paper_summaries(db: Session, staff_id: str, recent: bool = False, cited: bool = False) -> list[PaperSummary]:
    stmt = select(Paper).where(Paper.staff_id == staff_id)
    if recent:
        stmt = stmt.order_by(Paper.year.desc().nullslast(), Paper.citation_count.desc())
    elif cited:
        stmt = stmt.order_by(Paper.citation_count.desc(), Paper.year.desc().nullslast())
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
    return (
        f"{staff.name} is relevant for {company.company_name} because their research aligns with "
        f"{company.primary_sector.lower()} themes such as {', '.join((profile.technical_tags or [])[:3]) or 'adjacent technical work'}. "
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
    return 1.0 if lowered in normalized else 0.0


def _multi_overlap(left: list[str], right: list[str]) -> float:
    if not left or not right:
        return 0.0
    left_norm = {item.strip().lower() for item in left if item.strip()}
    right_norm = {item.strip().lower() for item in right if item.strip()}
    if not left_norm or not right_norm:
        return 0.0
    return len(left_norm & right_norm) / len(left_norm | right_norm)


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
