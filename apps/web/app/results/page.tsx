import { ResearcherCard } from "@/components/researcher-card";
import type { CompanyMatchResponse } from "@/lib/types";


const API_BASE_URL =
  process.env.API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8001";


async function getMatches(searchParams: Record<string, string | string[] | undefined>) {
  const company_name = typeof searchParams.company_name === "string" ? searchParams.company_name : "";
  const ticker = typeof searchParams.ticker === "string" ? searchParams.ticker : "";
  const company_description =
    typeof searchParams.company_description === "string" ? searchParams.company_description : "";

  if (!company_name || !company_description) {
    return null;
  }

  const response = await fetch(`${API_BASE_URL}/company/match`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      company_name,
      ticker: ticker || null,
      company_description,
    }),
    cache: "no-store",
  });

  if (!response.ok) {
    return null;
  }

  return (await response.json()) as CompanyMatchResponse;
}


export default async function ResultsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const resolved = await searchParams;
  const data = await getMatches(resolved);

  if (!data) {
    return (
      <section className="section">
        <div className="card">
          <h1 className="section-title">No company query yet</h1>
          <p className="muted">
            Start from the homepage with a company name and a few sentences about the company.
          </p>
        </div>
      </section>
    );
  }

  return (
    <>
      <section className="hero">
        <div>
          <p className="pill">{data.company.primary_sector}</p>
          <h1>{data.company.company_name}</h1>
          <p>{data.company.research_need_summary}</p>
          <div className="pill-row">
            {data.company.school_affinities.map((school) => (
              <span key={school} className="pill">
                {school}
              </span>
            ))}
          </div>
        </div>
      </section>
      <section className="section">
        <div className="split">
          <div className="card">
            <h2 className="section-title">Company Interpretation</h2>
            <p className="muted">Primary sector: {data.company.primary_sector}</p>
            <p className="muted">Confidence: {data.company.confidence}</p>
            <p className="muted">Matches returned: {data.matches.length}</p>
            <div className="pill-row">
              {data.company.technical_themes.map((theme) => (
                <span key={theme} className="pill">
                  {theme}
                </span>
              ))}
            </div>
          </div>
          <div className="card">
            <h2 className="section-title">How to read these matches</h2>
            <p className="muted">
              The top cards balance embedding similarity, research themes, publication evidence, and recency. Open the researcher detail page to inspect the full paper corpus and collaborator context before reaching out.
            </p>
          </div>
        </div>
      </section>
      <section className="section">
        {data.matches.length ? (
          <div className="card-grid dashboard-grid">
            {data.matches.map((match) => (
              <ResearcherCard
                key={match.staff_id}
                researcher={match}
                companyName={data.company.company_name}
              />
            ))}
          </div>
        ) : (
          <div className="card">
            <h2 className="section-title">No strong researcher matches yet</h2>
            <p className="muted">
              Try adding more technical detail about the company&rsquo;s products, workflows, or underlying methods so the embedding step has more research signal to work with.
            </p>
          </div>
        )}
      </section>
    </>
  );
}
