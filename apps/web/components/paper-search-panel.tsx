"use client";

import { useEffect, useMemo, useState } from "react";

import type { PaperSummary } from "@/lib/types";


type PaperListResponse = {
  staff_id: string;
  total: number;
  items: PaperSummary[];
};


const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8001";


export function PaperSearchPanel({ staffId }: { staffId: string }) {
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("recent");
  const [items, setItems] = useState<PaperSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const queryString = useMemo(() => {
    const params = new URLSearchParams({ sort, limit: "20" });
    if (search.trim()) {
      params.set("search", search.trim());
    }
    return params.toString();
  }, [search, sort]);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError("");
      try {
        const response = await fetch(`${API_BASE_URL}/staff/${staffId}/papers?${queryString}`);
        if (!response.ok) {
          throw new Error("Unable to load papers.");
        }
        const payload = (await response.json()) as PaperListResponse;
        if (!active) {
          return;
        }
        setItems(payload.items);
        setTotal(payload.total);
      } catch (_error) {
        if (!active) {
          return;
        }
        setItems([]);
        setTotal(0);
        setError("Unable to load papers right now.");
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [staffId, queryString]);

  return (
    <div className="card">
      <div className="split">
        <label>
          Search papers
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search by title, abstract, or summary"
          />
        </label>
        <label>
          Sort
          <select value={sort} onChange={(event) => setSort(event.target.value)}>
            <option value="recent">Most Recent</option>
            <option value="cited">Most Cited</option>
          </select>
        </label>
      </div>
      <p className="muted">Showing {items.length} of {total} papers.</p>
      {loading ? <p className="muted">Loading papers...</p> : null}
      {error ? <p className="muted">{error}</p> : null}
      <div className="paper-list">
        {items.length ? (
          items.map((paper) => (
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
          <p className="muted">No papers matched this search yet.</p>
        )}
      </div>
    </div>
  );
}
