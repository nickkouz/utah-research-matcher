
# Utah Research Matcher

This repo is being replatformed into a company-to-researcher discovery product for the University of Utah.

The new system accepts:

- required company name
- optional ticker symbol
- a free-text description of what the company does

Then it:

1. interprets the company into a structured research-facing profile
2. embeds that profile into vectors
3. matches it against precomputed University of Utah researcher vectors
4. returns the most relevant researchers, recent papers, most cited papers, direct links, and outreach talking points

## Target architecture

```text
apps/
  api/      FastAPI backend, SQLAlchemy models, Alembic migrations
  web/      Next.js frontend for company search, results, and researcher detail
workers/    Offline ingestion, OpenAlex resolution, enrichment, embeddings
shared/     Shared contracts and taxonomies
infra/      Environment and deployment helpers
docs/       Architecture notes
```

Core infrastructure:

- `Postgres + pgvector`
- `profiles.faculty.utah.edu` for researcher identity and affiliation data
- `OpenAlex` for publication metadata and citation counts
- embedding-first retrieval with LLM reranking

## Current direction

Phase 1 focuses on:

- all University of Utah schools
- everyone ingested from `profiles.faculty.utah.edu` into the registry
- only researchers with enough publication signal marked eligible for matching
- full searchable paper corpus per researcher
- two evidence sections on the detail page:
  - `Most Recent`
  - `Most Cited`

Phase 2 will expand to:

- the rest of the registry, even with weaker publication signal
- browsing by sector
- saved searches and saved researchers
- broader collaborator exploration

## Backend

The new backend lives in `apps/api`.

Key parts:

- FastAPI routes under `apps/api/app/api/routes`
- SQLAlchemy models under `apps/api/app/models`
- Alembic migrations under `apps/api/alembic`
- retrieval and interpretation services under `apps/api/app/services`

Primary endpoints:

- `POST /company/interpret`
- `POST /company/match`
- `GET /staff/{id}`
- `GET /staff/{id}/papers`
- `GET /staff/{id}/collaborators`
- `GET /diagnostics/summary`

## Frontend

The new frontend lives in `apps/web`.

Planned product pages:

- `/` company search homepage
- `/results` ranked researcher results
- `/staff/[id]` researcher detail page

## Workers

The offline data pipeline now belongs in `workers/`:

- `ingest_profiles`
- `import_csv`
- `resolve_openalex`
- `ingest_papers`
- `enrich_research`
- `generate_embeddings`

## Environment

Copy `.env.example` to `.env` and fill in:

- `OPENAI_API_KEY`
- `OPENAI_GENERATION_MODEL`
- `OPENAI_EMBEDDING_MODEL`
- `DATABASE_URL`
- `OPENALEX_API_KEY`
- `OPENALEX_CONTACT_EMAIL`
- `PROFILES_BASE_URL`
- `PROFILES_SEED_URLS`
- `API_BASE_URL`
- `NEXT_PUBLIC_API_BASE_URL`

## Local development

Start Postgres + pgvector:

```powershell
powershell -ExecutionPolicy Bypass -File infra/scripts/start-db.ps1
```

Start the API:

```powershell
Set-Location apps/api
pip install -e .
alembic upgrade head
python -m uvicorn app.main:app --reload --port 8001
```

If your shell Python cannot find the backend dependencies reliably, set up the dedicated API virtual environment first:

```powershell
powershell -ExecutionPolicy Bypass -File .\infra\scripts\setup-api-env.ps1
```

Start the web app:

```powershell
Set-Location apps/web
npm install
npm run dev
```

Verify the local API once it is running:

```powershell
cd "C:\Users\kouze\Codex Hackathon"
powershell -ExecutionPolicy Bypass -File .\infra\scripts\check-local-api.ps1
```

Inspect database coverage:

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8001/diagnostics/summary" -UseBasicParsing |
  Select-Object -ExpandProperty Content
```

## Next steps

1. Stand up Postgres with `pgvector`
2. Run Alembic migrations from `apps/api`
3. Build the Utah profiles ingestion worker
4. Resolve OpenAlex authors and ingest publications
5. Enrich summaries and generate embeddings
6. Wire the Next.js frontend to the live FastAPI backend

See `docs/replatform-architecture.md` for the current replatform notes.
See `docs/deployment-checklist.md` for the split frontend/backend deployment setup.

## Worker pipeline

Recommended local run order:

```powershell
Set-Location apps/api
pip install -e .
alembic upgrade head

Set-Location ..\..
python -m workers.ingest_profiles.run --limit 25
python -m workers.import_csv.run --csv-path data/raw/faculty_db.csv --limit 100
python -m workers.resolve_openalex.run --limit 25
python -m workers.ingest_papers.run --limit 25
python -m workers.enrich_research.run --limit 25
python -m workers.generate_embeddings.run --limit 25
```

To backfill a larger dataset into whichever database your current `DATABASE_URL` points at, use:

```powershell
powershell -ExecutionPolicy Bypass -File .\infra\scripts\setup-api-env.ps1
powershell -ExecutionPolicy Bypass -File .\infra\scripts\run-data-backfill.ps1 -ResolveLimit 250 -PaperLimit 250 -EnrichLimit 50 -EmbeddingLimit 250 -RefreshOpenAlex
```

To backfill a production database such as Railway Postgres from your machine, pass the target database URL explicitly and run multiple passes:

```powershell
powershell -ExecutionPolicy Bypass -File .\infra\scripts\run-data-backfill.ps1 `
  -DatabaseUrl "postgresql+psycopg://USER:PASSWORD@HOST:PORT/DBNAME" `
  -Passes 4 `
  -ResolveLimit 500 `
  -PaperLimit 500 `
  -EnrichLimit 100 `
  -EmbeddingLimit 500 `
  -RefreshOpenAlex
```

After each pass, the script prints a database snapshot so you can watch:

- `staff_registry`
- `staff_match_profiles`
- `staff_with_publication_signal`
- `openalex_resolved_profiles`
- `profiles_with_papers`
- `papers`
- `paper_authors`

When the database is filled correctly:

- `/researchers` should show multiple schools without requiring a company search
- `/diagnostics/summary` should show broad school coverage
- company search should stop collapsing onto a tiny subset of faculty

## Weekly sync

The repo now includes a weekly sync wrapper and a GitHub Actions workflow so the research layer can keep growing after the first backfill:

- local/manual wrapper: `infra/scripts/run-weekly-sync.ps1`
- GitHub Actions workflow: `.github/workflows/weekly-research-sync.yml`

The weekly sync is designed to:

1. refresh the staff registry from the CSV
2. resolve more staff to OpenAlex authors
3. ingest newly available papers
4. enrich newly changed records
5. generate embeddings for newly changed records

To run it manually against a target database:

```powershell
powershell -ExecutionPolicy Bypass -File .\infra\scripts\run-weekly-sync.ps1 `
  -DatabaseUrl "postgresql+psycopg://USER:PASSWORD@HOST:PORT/DBNAME"
```

To run it automatically in GitHub Actions, add these repository secrets:

- `DATABASE_URL`
- `OPENAI_API_KEY`
- `OPENALEX_API_KEY`
- `OPENALEX_CONTACT_EMAIL`

The workflow runs every Monday and can also be triggered manually with `workflow_dispatch`.

That sequence will:

1. pull people from `profiles.faculty.utah.edu` into `staff_registry`
2. optionally bootstrap existing staff metadata from `faculty_db.csv`
3. resolve publication-backed researchers through OpenAlex
4. ingest all available papers for matched researchers
5. generate summaries and tags
6. write pgvector embeddings for retrieval
