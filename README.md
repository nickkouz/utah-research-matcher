# Utah Research Matcher

A Codex-powered agent that matches University of Utah undergraduates with faculty researchers whose active work aligns with the student's interests, and drafts personalized cold emails for outreach.

Built for the Build with AI Codex Hackathon.

## The problem

Utah has 25,000+ undergraduates. Most never do research, often because they do not know how to find a professor whose work fits their interests, and they do not know how to write a good cold email. Discovery takes weeks of scrolling through department pages. Email drafts get ignored because they sound generic.

## What this does

1. Student fills out a short intake form describing their major, interests, skills, and goals.
2. The system matches them to the top 5 faculty whose active research best fits their profile, using semantic embeddings rather than keyword search.
3. For each match, it drafts three personalized cold emails in different modes: coffee chat, lab inquiry, and paper response.
4. The student picks the email they like and pastes it into their email client.

Discovery time: weeks to minutes.

## Pipeline

```text
Form input
  -> Normalize profile (LLM)
  -> Match against pre-embedded faculty database (cosine similarity)
  -> Top 5 faculty
  -> Generate match rationale per faculty (LLM, parallel)
  -> Generate 3 email modes per faculty (LLM, parallel, 15 total)
  -> Critic review + revise (LLM, parallel)
  -> Results page with toggleable emails
```

## Repo structure

```text
/scraper         Faculty data collection
/pipeline        AI pipeline and orchestration
  /prompts       LLM prompts loaded at runtime
/frontend        Demo UI
/data            Demo student and faculty datasets
AGENTS.md        Context file for AI coding assistants
README.md        This file
```

## Prompt files

The prompt templates live under `pipeline/prompts/` and are loaded at runtime by the pipeline. The Stage 1 normalizer prompt is stored in `pipeline/prompts/01_normalizer.md`.

## Getting started

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m pipeline.orchestrator
```

The generated demo output is written to `data/demo_results.json`. Open `frontend/results.html` using a local static server to view the demo cards.

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

MVP scaffold complete. Live scraping, embedding calls, and richer faculty enrichment are the next steps.
