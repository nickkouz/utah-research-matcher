# Team Plan

## Team split

### Staff database owner

Primary responsibility:
- Scrape Utah faculty profiles
- Extract names, departments, emails, profile URLs, bios, and recent publication metadata
- Produce a stable `faculty_db.json` schema for the pipeline

Initial tasks:
1. Expand `scraper/scraper.py` to collect faculty profile URLs from seed pages.
2. Build parsing logic for faculty name, title, department, email, and bio.
3. Save output to `data/faculty_db.json` using the schema in `AGENTS.md`.
4. Keep `data/fallback_db.json` updated enough for demo fallback.

Definition of done:
- `data/faculty_db.json` exists locally and follows the agreed schema
- At least one real Utah department is scraped successfully
- Output is documented if any fields are missing or nullable

### Pipeline owner

Primary responsibility:
- Normalize the student profile
- Rank faculty matches
- Generate match rationales and personalized outreach emails
- Orchestrate the full pipeline from form input to results JSON

Initial tasks:
1. Improve `pipeline/normalizer.py` so the summary reads like a research profile.
2. Replace heuristic ranking in `pipeline/ranker.py` with embeddings when API wiring is ready.
3. Upgrade `pipeline/emailer.py` to use prompt-driven generation.
4. Keep `pipeline/orchestrator.py` runnable end-to-end against `data/fallback_db.json`.

Definition of done:
- `python -m pipeline.orchestrator` produces a complete results object
- Top 5 matches render with rationale and email content
- Pipeline still works even if real scraped data is not ready

## Shared checkpoints

1. Agree on the faculty record schema before major implementation diverges.
2. Integrate using `data/fallback_db.json` first.
3. Merge the real faculty database only after the pipeline reads it without schema changes.
4. Rehearse the demo with both the real path and the fallback path.

## Recommended branch names

- `staff-db/seed-scraper`
- `staff-db/faculty-parser`
- `pipeline/normalizer-upgrade`
- `pipeline/embedding-ranker`
- `integration/demo-polish`
