import Link from "next/link";

import type { StaffBrowseItem } from "@/lib/types";


export function StaffBrowserCard({ researcher }: { researcher: StaffBrowseItem }) {
  return (
    <article className="match-card">
      <div className="pill-row">
        {researcher.eligible_for_matching ? (
          <span className="score-label">Match Ready</span>
        ) : (
          <span className="pill neutral-pill">Registry Only</span>
        )}
        <span className="pill">{researcher.primary_school ?? "University of Utah"}</span>
        {researcher.department ? <span className="pill">{researcher.department}</span> : null}
      </div>
      <h3>{researcher.name}</h3>
      <p className="muted">{researcher.title}</p>
      <p>{researcher.ai_research_summary}</p>
      <div className="browser-stats">
        <div className="mini-evidence-item">
          <strong>Papers</strong>
          <div>{researcher.publication_count}</div>
        </div>
        <div className="mini-evidence-item">
          <strong>Citations</strong>
          <div>{researcher.citation_count_total}</div>
        </div>
        <div className="mini-evidence-item">
          <strong>Last Active</strong>
          <div>{researcher.last_active_year ?? "Unknown"}</div>
        </div>
      </div>
      <div className="cta-row">
        <Link className="button" href={`/staff/${researcher.staff_id}`}>
          View Researcher Detail
        </Link>
        <a className="button-secondary" href={researcher.profile_url} target="_blank" rel="noreferrer">
          Utah Profile
        </a>
        {researcher.lab_url ? (
          <a className="button-secondary" href={researcher.lab_url} target="_blank" rel="noreferrer">
            Lab Website
          </a>
        ) : null}
      </div>
    </article>
  );
}
