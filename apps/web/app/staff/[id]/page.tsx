import Link from "next/link";

import { PaperSearchPanel } from "@/components/paper-search-panel";
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
        {papers.length ? (
          papers.map((paper) => (
            <div key={paper.id} className="paper-item">
              <strong>{paper.title}</strong>
              <div className="muted">
                {paper.year ?? "Year unknown"}
                {paper.venue ? ` - ${paper.venue}` : ""}
                {" - "}Citations: {paper.citation_count}
              </div>
              {paper.ai_summary ? <p>{paper.ai_summary}</p> : null}
              <div className="paper-links">
                {paper.paper_url ? (
                  <a href={paper.paper_url} target="_blank" rel="noreferrer">
                    Paper link
                  </a>
                ) : null}
                {paper.pdf_url ? (
                  <a href={paper.pdf_url} target="_blank" rel="noreferrer">
                    PDF
                  </a>
                ) : null}
              </div>
            </div>
          ))
        ) : (
          <p className="muted">No papers available in this view yet.</p>
        )}
      </div>
    </div>
  );
}


function CollaboratorList({
  title,
  collaborators,
}: {
  title: string;
  collaborators: CollaboratorSummary[];
}) {
  return (
    <div className="detail-panel">
      <h2 className="section-title">{title}</h2>
      {collaborators.length ? (
        <ul className="collaborator-list">
          {collaborators.map((collaborator) => (
            <li key={`${collaborator.name}-${collaborator.affiliation}`} className="collaborator-item">
              <strong>{collaborator.name}</strong>
              {collaborator.affiliation ? <div className="muted">{collaborator.affiliation}</div> : null}
              {collaborator.related_papers.length ? (
                <div className="muted">Related papers: {collaborator.related_papers.join("; ")}</div>
              ) : null}
            </li>
          ))}
        </ul>
      ) : (
        <p className="muted">No collaborators are available for this section yet.</p>
      )}
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

  const uofuCollaborators = detail.collaborators.filter((collaborator) => collaborator.is_uofu);
  const externalCollaborators = detail.collaborators.filter((collaborator) => !collaborator.is_uofu);

  return (
    <>
      <section className="hero">
        <div className="profile-hero">
          <div>
            <div className="pill-row">
              {(detail.school_affiliations ?? []).map((school) => (
                <span key={school} className="pill">
                  {school}
                </span>
              ))}
            </div>
            <h1>{detail.name}</h1>
            <p className="muted">{detail.title}</p>
            <p>{detail.ai_research_summary}</p>
            <div className="cta-row">
              <a className="button" href={detail.profile_url} target="_blank" rel="noreferrer">
                Open Utah Profile
              </a>
              {detail.lab_url ? (
                <a className="button-secondary" href={detail.lab_url} target="_blank" rel="noreferrer">
                  Lab Website
                </a>
              ) : null}
              <Link className="button-secondary" href="/results">
                Back to Results
              </Link>
            </div>
          </div>
          {detail.image_url ? (
            <div className="profile-image-shell">
              <img src={detail.image_url} alt={detail.name} className="profile-image" />
            </div>
          ) : null}
        </div>
      </section>

      <section className="section detail-layout">
        <div className="results-layout">
          <div className="card profile-meta-grid">
            <div>
              <strong>Department</strong>
              <div className="muted">{detail.department ?? "Not available"}</div>
            </div>
            <div>
              <strong>Email</strong>
              <div className="muted">{detail.email ?? "Not available"}</div>
            </div>
            <div>
              <strong>School affiliations</strong>
              <div className="muted">{detail.school_affiliations.join(", ") || "Not available"}</div>
            </div>
            <div>
              <strong>Indexed papers</strong>
              <div className="muted">{detail.searchable_papers_count}</div>
            </div>
          </div>
          {detail.bio ? (
            <div className="card">
              <h2 className="section-title">Profile Context</h2>
              <p>{detail.bio}</p>
            </div>
          ) : null}
          <div className="split">
            <PaperColumn title="Most Recent" papers={detail.recent_papers} />
            <PaperColumn title="Most Cited" papers={detail.most_cited_papers} />
          </div>
          <div className="card">
            <h2 className="section-title">Searchable Paper Corpus</h2>
            <p className="muted">
              This researcher currently has {detail.searchable_papers_count} papers in the database.
            </p>
          </div>
          <PaperSearchPanel staffId={detail.staff_id} />
        </div>
        <aside className="results-layout">
          <div className="detail-panel">
            <h2 className="section-title">Key Outreach Points</h2>
            {detail.key_outreach_points.length ? (
              <ul>
                {detail.key_outreach_points.map((point) => (
                  <li key={point}>{point}</li>
                ))}
              </ul>
            ) : (
              <p className="muted">Outreach guidance will appear here once the backend generates it.</p>
            )}
          </div>
          <CollaboratorList title="University of Utah Collaborators" collaborators={uofuCollaborators} />
          <CollaboratorList title="External Collaborators" collaborators={externalCollaborators} />
        </aside>
      </section>
    </>
  );
}
