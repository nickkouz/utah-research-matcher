# Deployment Checklist

This project is a monorepo with two separate deploy targets:

- `apps/web` -> Next.js frontend
- `apps/api` -> FastAPI backend

Do not try to deploy the repo root as a single Vercel app.

## Frontend on Vercel

Create a Vercel project with:

- **Root Directory**: `apps/web`
- **Framework Preset**: `Next.js`
- **Install Command**: `npm install`
- **Build Command**: `npm run build`

Frontend environment variables:

- `NEXT_PUBLIC_API_BASE_URL=https://YOUR-BACKEND-DOMAIN`
- `API_BASE_URL=https://YOUR-BACKEND-DOMAIN`

Notes:

- `NEXT_PUBLIC_API_BASE_URL` is used by client components.
- `API_BASE_URL` is used by server-rendered pages.
- Do not leave either value pointed at `http://127.0.0.1:8001` in production.

## Backend deployment

Deploy `apps/api` separately on a Python-friendly platform such as Railway, Render, or Fly.

Backend environment variables:

- `OPENAI_API_KEY`
- `OPENAI_GENERATION_MODEL=gpt-5-mini`
- `OPENAI_EMBEDDING_MODEL=text-embedding-3-small`
- `OPENALEX_API_KEY`
- `OPENALEX_CONTACT_EMAIL`
- `DATABASE_URL`
- `PROFILES_BASE_URL=https://profiles.faculty.utah.edu`
- `PROFILES_SEED_URLS=https://profiles.faculty.utah.edu`

The backend needs a Postgres database with the `vector` extension enabled.

## Database

For local development, the repo uses Docker Compose:

```powershell
cd "C:\Users\kouze\Codex Hackathon"
powershell -ExecutionPolicy Bypass -File .\infra\scripts\start-db.ps1
```

Then run migrations:

```powershell
cd "C:\Users\kouze\Codex Hackathon\apps\api"
python -m alembic upgrade head
```

## First local data build

```powershell
cd "C:\Users\kouze\Codex Hackathon"
python -m workers.import_csv.run --csv-path data/raw/faculty_db.csv --limit 100
python -m workers.resolve_openalex.run --limit 25 --refresh
python -m workers.ingest_papers.run --limit 25
python -m workers.enrich_research.run --limit 5
python -m workers.generate_embeddings.run --limit 25
```

Recommended batching:

- keep OpenAI-backed enrichment small at first (`5` or `10`) to reduce `429` rate limits
- paper ingestion and embedding generation can usually run at `25`

## Pre-deploy verification

Before deploying, confirm:

1. the database is populated with paper-backed researchers
2. the backend can interpret a company and return matches
3. the frontend env vars point to the deployed backend URL
4. Vercel is configured with `apps/web` as the root directory
