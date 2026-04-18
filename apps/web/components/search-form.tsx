"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";


export function SearchForm() {
  const router = useRouter();
  const [companyName, setCompanyName] = useState("");
  const [ticker, setTicker] = useState("");
  const [description, setDescription] = useState("");
  const descriptionLength = description.trim().length;
  const descriptionReady = descriptionLength >= 40;

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedCompanyName = companyName.trim();
    const trimmedDescription = description.trim();
    const params = new URLSearchParams({
      company_name: trimmedCompanyName,
      company_description: trimmedDescription,
    });
    if (ticker.trim()) {
      params.set("ticker", ticker.trim());
    }
    router.push(`/results?${params.toString()}`);
  }

  return (
    <form className="search-form card" onSubmit={onSubmit}>
      <label>
        Company Name
        <input
          value={companyName}
          onChange={(event) => setCompanyName(event.target.value)}
          placeholder="Example: Recursion, Adobe, Delta"
          required
        />
      </label>
      <label>
        Ticker Symbol (optional)
        <input
          value={ticker}
          onChange={(event) => setTicker(event.target.value)}
          placeholder="Example: MSFT"
        />
      </label>
      <label>
        Company Description
        <textarea
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          placeholder="Describe what the company does, what products it makes, and what technical or market problems it works on."
          minLength={40}
          required
        />
      </label>
      <div className="form-help">
        <strong>Better input leads to better matches.</strong>
        <p className="muted">
          Include the company&rsquo;s products, technical stack, customer problems, and the sector it operates in.
        </p>
        <div className="pill-row">
          <span className="pill">Example: digital therapeutics platform for chronic disease monitoring</span>
          <span className="pill">Example: grid software for battery dispatch and energy forecasting</span>
        </div>
        <p className="muted">Description length: {descriptionLength} characters</p>
      </div>
      <div className="cta-row">
        <button className="button" type="submit" disabled={!companyName.trim() || !descriptionReady}>
          Find Utah Researchers
        </button>
      </div>
    </form>
  );
}
