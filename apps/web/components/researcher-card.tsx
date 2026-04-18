import Link from "next/link";

import type { StaffSummaryResponse } from "@/lib/types";


export function ResearcherCard({
  researcher,
  companyName,
}: {
  researcher: StaffSummaryResponse;
  companyName: string;
}) {
  return (
    <article className="match-card">
      <div className="pill-row">
        <span className="score-label">Score {researcher.score.toFixed(2)}</span>
        <span className="pill">{researcher.primary_school ?? "University of Utah"}</span>
        {researcher.department ? <span className="pill">{researcher.department}</span> : null}
      </div>
      <h3>{researcher.name}</h3>
      <p className="muted">{researcher.title}</p>
      {researcher.school_affiliations.length > 1 ? (
        <p className="muted">Also affiliated with {researcher.school_affiliations.slice(1).join(", ")}.</p>
      ) : null}
      <p>{researcher.ai_research_summary}</p>
      <p className="muted">{researcher.match_reason}</p>
      <div className="mini-evidence">
        {researcher.recent_papers[0] ? (
          <div className="mini-evidence-item">
            <strong>Most Recent</strong>
            <div>{researcher.recent_papers[0].title}</div>
            <div className="muted">{researcher.recent_papers[0].year ?? "Year unknown"}</div>
          </div>
        ) : null}
        {researcher.most_cited_papers[0] ? (
          <div className="mini-evidence-item">
            <strong>Most Cited</strong>
            <div>{researcher.most_cited_papers[0].title}</div>
            <div className="muted">Citations: {researcher.most_cited_papers[0].citation_count}</div>
          </div>
        ) : null}
      </div>
      <div className="cta-row">
        <Link
          className="button"
          href={`/staff/${researcher.staff_id}?company=${encodeURIComponent(companyName)}`}
        >
          View Researcher Detail
        </Link>
        {researcher.lab_url ? (
          <a className="button-secondary" href={researcher.lab_url} target="_blank" rel="noreferrer">
            Lab Website
          </a>
        ) : null}
      </div>
    </article>
  );
}
