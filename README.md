
# Utah Research Matcher

A Codex-powered agent that matches University of Utah undergraduates with faculty researchers whose active work aligns with the student's interests, and drafts personalized cold emails for outreach.

Built for the Build with AI Codex Hackathon.

## The problem

Utah has 25,000+ undergraduates. Most never do research, often because they do not know how to find a professor whose work fits their interests, and they do not know how to write a good cold email. Discovery takes weeks of scrolling through department pages. Email drafts get ignored because they sound generic.

## What this does

1. Student opens a dashboard to resume an unfinished form, revisit recent faculty matches, and browse the full faculty directory.
2. Student fills out a structured research form with research topic, methods, application areas, and relevant examples.
3. The system normalizes the profile, asks one follow-up if the input is still too vague, and then matches the student to the top 5 faculty whose active research best fits the profile.
4. For each match, it drafts three personalized cold emails in different modes: coffee chat, lab inquiry, and paper response.
5. The student picks the email they like and pastes it into their email client.

Discovery time: weeks to minutes.

## Pipeline

```text
Form input
  -> Normalize profile into research facets (LLM + fallback rules)
  -> Follow-up gate for vague profiles
  -> Load faculty dataset
  -> Hybrid retrieval over faculty summaries, keywords, and paper text
  -> Precision-first rerank + diversity pass
  -> Top 5 faculty
  -> Generate match rationale per faculty (LLM, parallel)
  -> Generate 3 email modes per faculty (LLM, parallel, 15 total)
  -> Agent review + revise (LLM, parallel)
  -> Results page with toggleable emails
```

## Product overview

The product has two main application surfaces:

1. Student dashboard homepage
2. Student research form
3. Results page

Planned user flow:

1. Student lands on the dashboard.
2. Student opens or resumes a research match form.
3. Student submits academic background, methods, application areas, and research interests.
4. The pipeline either asks one follow-up or produces top faculty matches plus presentable email drafts.
5. Student can revisit recent results and browse all faculty from the homepage.

Near-term application sections:

- Dashboard with entry points to start or resume a form, revisit recent faculty matches, and browse the complete faculty directory.
- Form experience with stronger signal capture: research topic, methods, application areas, and reference examples.

Deferred item:

- UNID login is acknowledged in the product vision but should not be implemented yet for the hackathon MVP.

## Repo structure

```text
/scraper         Faculty data collection
/pipeline        AI pipeline and orchestration
  /prompts       LLM prompts loaded at runtime
/frontend        Shared JS, CSS, and assets
/form            Student form route
/results         Results route
/data            Demo student, faculty, and browser payload datasets
/evals           Matching evaluation cases
index.html       Dashboard route
AGENTS.md        Context file for AI coding assistants
README.md        This file
```

## Prompt files

The prompt templates live under `pipeline/prompts/` and are loaded at runtime by the pipeline. The Stage 1 normalizer prompt is stored in `pipeline/prompts/01_normalizer.md`.

## Pipeline contracts

The canonical stage-by-stage JSON contracts live in `PIPELINE_CONTRACTS.md`. Both the dataset workflow and the pipeline workflow should integrate against that file.

## Getting started

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python dev_server.py
```

Then open `http://127.0.0.1:8000`.

The generated demo output is written to `data/demo_results.json`. The app will automatically use `data/faculty_db.json` if present, and otherwise fall back to `data/fallback_db.json`.

To regenerate the faculty browser payload:

```bash
python -m pipeline.build_browser_payload
```

To run the lightweight matching eval harness:

```bash
python -m pipeline.evaluate_matches
```

## Deployment notes

The app is structured to deploy on Vercel with:

- static dashboard, form, and results pages at `/`, `/form`, and `/results`
- a single Python API function at `api/index.py`
- a rewrite from `/api/match` to `/api` in `vercel.json`
- static faculty browser payload in `data/faculty_browser.json`

For model-backed generation and embeddings in deployment, set:

- `OPENAI_API_KEY`

If `OPENAI_API_KEY` is missing, the app still runs using fallback ranking and template/rule-based generation.

## Team workflow

This repo is organized for a two-person team with clear ownership:

- Staff database owner: scrape Utah faculty pages, build structured faculty records, and maintain `data/fallback_db.json` plus the full faculty database.
- Pipeline owner: normalize the student profile, rank faculty matches, generate rationales and emails, and maintain the orchestration flow.

Recommended branch names:

- `main` for the demo-ready branch
- `staff-db/<task-name>` for scraping and data work
- `pipeline/<task-name>` for matching and prompt work
- `integration/<task-name>` for merge fixes and demo polish

Working agreement:

1. Keep `data/fallback_db.json` usable at all times so the demo never depends on unfinished scraping.
2. The database owner should publish stable faculty record JSON that the pipeline can consume without custom glue.
3. The pipeline owner should keep everything runnable against the fallback dataset while the real faculty database is being built.
4. Merge through small PRs and re-run the end-to-end demo after each integration.

## Tech stack

- Python 3.11+ for backend and pipeline
- OpenAI API for generation and embeddings
- BeautifulSoup or Playwright for scraping
- Plain HTML, CSS, and JavaScript for the demo frontend

## Status

Revised MVP implemented:

- student-facing dashboard homepage
- structured form with autosave, specificity meter, and follow-up gating
- hybrid retrieval pipeline with richer faculty normalization, reranking, and diversity pass
- faculty browser payload and lightweight eval harness

Next major step: replace the fallback faculty dataset with the full scraped and enriched Utah faculty database.
