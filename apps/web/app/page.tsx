import { SearchForm } from "@/components/search-form";


export default function HomePage() {
  return (
    <>
      <section className="hero">
        <div>
          <p className="pill">University of Utah Research Discovery</p>
          <h1>Find the Utah researchers most relevant to a public company.</h1>
          <p>
            Enter a company name, optional ticker, and a plain-English description of what the
            company does. The system interprets the company, embeds the research themes, and finds
            the closest University of Utah researchers based on publications, research summaries,
            and citation-backed evidence.
          </p>
        </div>
      </section>

      <section className="section">
        <div className="split">
          <SearchForm />
          <div className="card">
            <h2 className="section-title">What the new platform is optimizing for</h2>
            <div className="metric-list">
              <div className="metric">
                <strong>Embedding-first retrieval</strong>
                <div className="muted">Company vectors match against precomputed researcher vectors.</div>
              </div>
              <div className="metric">
                <strong>Publication-backed evidence</strong>
                <div className="muted">All papers come from the OpenAlex-backed research layer.</div>
              </div>
              <div className="metric">
                <strong>Actionable researcher profiles</strong>
                <div className="muted">Recent papers, most cited work, links, and outreach guidance.</div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}

