import Link from "next/link";

import type { CollaboratorSummary, PaperSummary, StaffSummaryResponse } from "@/lib/types";


const API_BASE_URL =
  process.env.API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8001";

type StaffDetail = Omit<StaffSummaryResponse, "match_reason" | "score" | "further_contacts"> & {
  email?: string | null;
  profile_url: string;
  bio?: string | null;
  searchable_papers_count: number;
  collaborators: CollaboratorSummary[];
};


async function getStaffDetail(id: string) {
  const response = await fetch(`${API_BASE_URL}/staff/${id}`, { cache: "no-store" });
  if (!response.ok) {
    return null;
  }
  return (await response.json()) as StaffDetail;
}


function PaperColumn({ title, papers }: { title: string; papers: PaperSummary[] }) {
  return (
    <div className="card">
      <h2 className="section-title">{title}</h2>
      <div className="paper-list">
        {papers.map((paper) => (
          <div key={paper.id} className="paper-item">
            <strong>{paper.title}</strong>
            <div className="muted">
              {paper.year ?? "Year unknown"}{paper.venue ? ` · ${paper.venue}` : ""} · Citations:{" "}
              {paper.citation_count}
            </div>
            {paper.ai_summary ? <p>{paper.ai_summary}</p> : null}
            <div className="paper-links">
              {paper.paper_url ? <a href={paper.paper_url}>Paper link</a> : null}
              {paper.pdf_url ? <a href={paper.pdf_url}>PDF</a> : null}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}


export default async function StaffDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const detail = await getStaffDetail(id);

  if (!detail) {
    return (
      <section className="section">
        <div className="card">
          <h1 className="section-title">Researcher not found</h1>
          <p className="muted">This detail page will populate once the backend has researcher data.</p>
        </div>
      </section>
    );
  }

  return (
    <>
      <section className="hero">
        <div>
          <div className="pill-row">
            {(detail.school_affiliations ?? []).map((school) => (
              <span key={school} className="pill">
                {school}
              </span>
            ))}
          </div>
          <h1>{detail.name}</h1>
          <p>{detail.ai_research_summary}</p>
          <div className="cta-row">
            <a className="button" href={detail.profile_url}>
              Open Utah Profile
            </a>
            <Link className="button-secondary" href="/results">
              Back to Results
            </Link>
          </div>
        </div>
      </section>

      <section className="section detail-layout">
        <div className="results-layout">
          <div className="split">
            <PaperColumn title="Most Recent" papers={detail.recent_papers} />
            <PaperColumn title="Most Cited" papers={detail.most_cited_papers} />
          </div>
          <div className="card">
            <h2 className="section-title">Searchable Paper Corpus</h2>
            <p className="muted">
              This researcher currently has {detail.searchable_papers_count} papers in the database.
              The dedicated searchable list endpoint is wired on the backend and ready for UI filtering.
            </p>
          </div>
        </div>
        <aside className="results-layout">
          <div className="detail-panel">
            <h2 className="section-title">Key Outreach Points</h2>
            <ul>
              {detail.key_outreach_points.map((point) => (
                <li key={point}>{point}</li>
              ))}
            </ul>
          </div>
          <div className="detail-panel">
            <h2 className="section-title">Collaborators</h2>
            <ul>
              {detail.collaborators.map((collaborator) => (
                <li key={`${collaborator.name}-${collaborator.affiliation}`}>
                  {collaborator.name}
                  {collaborator.affiliation ? ` · ${collaborator.affiliation}` : ""}
                </li>
              ))}
            </ul>
          </div>
        </aside>
      </section>
    </>
  );
}
