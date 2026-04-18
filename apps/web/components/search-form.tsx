"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";


export function SearchForm() {
  const router = useRouter();
  const [companyName, setCompanyName] = useState("");
  const [ticker, setTicker] = useState("");
  const [description, setDescription] = useState("");

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const params = new URLSearchParams({
      company_name: companyName,
      company_description: description,
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
          required
        />
      </label>
      <div className="cta-row">
        <button className="button" type="submit">
          Find Utah Researchers
        </button>
      </div>
    </form>
  );
}

