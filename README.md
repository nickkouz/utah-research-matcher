
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

## Frontend

The new frontend lives in `apps/web`.

Planned product pages:

- `/` company search homepage
- `/results` ranked researcher results
- `/staff/[id]` researcher detail page

## Workers

The offline data pipeline now belongs in `workers/`:

- `ingest_profiles`
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

Start the web app:

```powershell
Set-Location apps/web
npm install
npm run dev
```

## Next steps

1. Stand up Postgres with `pgvector`
2. Run Alembic migrations from `apps/api`
3. Build the Utah profiles ingestion worker
4. Resolve OpenAlex authors and ingest publications
5. Enrich summaries and generate embeddings
6. Wire the Next.js frontend to the live FastAPI backend

See `docs/replatform-architecture.md` for the current replatform notes.

## Worker pipeline

Recommended local run order:

```powershell
Set-Location apps/api
pip install -e .
alembic upgrade head

Set-Location ..\..
python -m workers.ingest_profiles.run --limit 25
python -m workers.resolve_openalex.run --limit 25
python -m workers.ingest_papers.run --limit 25
python -m workers.enrich_research.run --limit 25
python -m workers.generate_embeddings.run --limit 25
```

That sequence will:

1. pull people from `profiles.faculty.utah.edu` into `staff_registry`
2. resolve publication-backed researchers through OpenAlex
3. ingest all available papers for matched researchers
4. generate summaries and tags
5. write pgvector embeddings for retrieval
