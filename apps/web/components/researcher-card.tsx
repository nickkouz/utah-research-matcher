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
        <span className="pill">{researcher.primary_school ?? "University of Utah"}</span>
        {researcher.department ? <span className="pill">{researcher.department}</span> : null}
      </div>
      <h3>{researcher.name}</h3>
      <p className="muted">{researcher.title}</p>
      <p>{researcher.ai_research_summary}</p>
      <p className="muted">{researcher.match_reason}</p>
      <div className="cta-row">
        <Link
          className="button"
          href={`/staff/${researcher.staff_id}?company=${encodeURIComponent(companyName)}`}
        >
          View Researcher Detail
        </Link>
      </div>
    </article>
  );
}

