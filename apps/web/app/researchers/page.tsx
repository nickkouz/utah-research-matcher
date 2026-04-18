import Link from "next/link";

import { StaffBrowserCard } from "@/components/staff-browser-card";
import type { StaffBrowseResponse } from "@/lib/types";


const API_BASE_URL =
  process.env.API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8001";


type PageProps = {
  searchParams?: Promise<{
    search?: string;
    school?: string;
    sort?: string;
    eligible_only?: string;
  }>;
};


async function getStaffDirectory(query: {
  search?: string;
  school?: string;
  sort?: string;
  eligible_only?: string;
}): Promise<StaffBrowseResponse> {
  const params = new URLSearchParams();
  if (query.search) params.set("search", query.search);
  if (query.school) params.set("school", query.school);
  if (query.sort) params.set("sort", query.sort);
  if (query.eligible_only === "true") params.set("eligible_only", "true");

  const url = `${API_BASE_URL}/staff${params.toString() ? `?${params}` : ""}`;
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Failed to load staff directory.");
  }
  return response.json();
}


export default async function ResearchersPage({ searchParams }: PageProps) {
  const params = (await searchParams) ?? {};
  const directory = await getStaffDirectory(params);

  return (
    <>
      <section className="hero compact-hero">
        <div>
          <p className="pill">Researcher Directory</p>
          <h1>Browse the Utah researcher database without running a company search.</h1>
          <p>
            This is the direct browser for the underlying database. Filter by school, search by
            name or topic, and jump straight into researcher detail pages.
          </p>
        </div>
      </section>

      <section className="section">
        <div className="split">
          <form className="card search-form" action="/researchers" method="get">
            <h2 className="section-title">Browse Filters</h2>
            <label>
              Search
              <input
                type="text"
                name="search"
                placeholder="Name, department, or research topic"
                defaultValue={params.search ?? ""}
              />
            </label>
            <label>
              School
              <select name="school" defaultValue={params.school ?? ""}>
                <option value="">All schools</option>
                {directory.available_schools.map((school) => (
                  <option key={school} value={school}>
                    {school}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Sort
              <select name="sort" defaultValue={params.sort ?? "papers"}>
                <option value="papers">Most papers</option>
                <option value="citations">Most citations</option>
                <option value="recent">Most recent activity</option>
                <option value="name">Alphabetical</option>
              </select>
            </label>
            <label className="checkbox-row">
              <input
                type="checkbox"
                name="eligible_only"
                value="true"
                defaultChecked={params.eligible_only === "true"}
              />
              <span>Only show match-ready researchers</span>
            </label>
            <div className="cta-row">
              <button className="button" type="submit">
                Update Directory
              </button>
              <Link className="button-secondary" href="/researchers">
                Clear Filters
              </Link>
            </div>
          </form>

          <div className="results-layout">
            <div className="card">
              <h2 className="section-title">Directory Snapshot</h2>
              <div className="metric-list">
                <div className="metric">
                  <strong>Total Researchers in View</strong>
                  <div className="muted">{directory.total}</div>
                </div>
                <div className="metric">
                  <strong>Current Filter</strong>
                  <div className="muted">
                    {params.school || params.search || params.eligible_only === "true"
                      ? [
                          params.search ? `Search: ${params.search}` : null,
                          params.school ? `School: ${params.school}` : null,
                          params.eligible_only === "true" ? "Match-ready only" : null,
                        ]
                          .filter(Boolean)
                          .join(" | ")
                      : "Showing the full database view."}
                  </div>
                </div>
              </div>
            </div>

            <div className="card-grid">
              {directory.items.map((researcher) => (
                <StaffBrowserCard key={researcher.staff_id} researcher={researcher} />
              ))}
              {directory.items.length === 0 ? (
                <div className="card">
                  <h2 className="section-title">No Researchers Found</h2>
                  <p className="muted">
                    Try a broader school selection or clear the search text to browse more of the
                    database.
                  </p>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
