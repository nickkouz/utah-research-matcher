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

Recommended first path: Railway for the API plus a pgvector-enabled Postgres service.

### Railway backend steps

1. Create a new Railway project.
2. Add a **pgvector Postgres** service, not plain Postgres.
3. Add a second service from your GitHub repo:
   - repo: `nickkouz/utah-research-matcher`
   - root directory: `apps/api`
4. The API service now includes `apps/api/railway.toml`, which defines the Railway build/start/healthcheck config in code.
5. In Railway, either let that file be auto-detected or explicitly set the Config as Code path to:

```text
/apps/api/railway.toml
```

6. If you want to keep the settings in the dashboard instead, set the build and start commands to:

```text
Build Command: pip install -r requirements.txt
Start Command: python main.py
```

If Railway auto-detects Python correctly, the committed `apps/api/requirements.txt` should also allow the service to install dependencies without a custom build command. Setting the build command explicitly is still the safest option.

The repo now includes `apps/api/main.py`, which runs Alembic migrations on startup and then starts Uvicorn on Railway's assigned `PORT`.
7. In the API service variables, set:
   - `OPENAI_API_KEY`
   - `OPENAI_GENERATION_MODEL=gpt-5-mini`
   - `OPENAI_EMBEDDING_MODEL=text-embedding-3-small`
   - `OPENALEX_API_KEY`
   - `OPENALEX_CONTACT_EMAIL`
   - `PROFILES_BASE_URL=https://profiles.faculty.utah.edu`
   - `PROFILES_SEED_URLS=https://profiles.faculty.utah.edu`
   - `CORS_ALLOWED_ORIGINS=https://YOUR-VERCEL-DOMAIN`
8. Set `DATABASE_URL` on the API service to the connection string from the pgvector Postgres service.
9. Generate a public domain for the API service in Railway networking.
10. Copy that public API URL into the Vercel frontend env vars:
   - `NEXT_PUBLIC_API_BASE_URL=https://YOUR-RAILWAY-API-DOMAIN`
   - `API_BASE_URL=https://YOUR-RAILWAY-API-DOMAIN`
11. Redeploy the Vercel frontend after the env vars are updated.

Backend environment variables:

- `OPENAI_API_KEY`
- `OPENAI_GENERATION_MODEL=gpt-5-mini`
- `OPENAI_EMBEDDING_MODEL=text-embedding-3-small`
- `OPENALEX_API_KEY`
- `OPENALEX_CONTACT_EMAIL`
- `DATABASE_URL`
- `PROFILES_BASE_URL=https://profiles.faculty.utah.edu`
- `PROFILES_SEED_URLS=https://profiles.faculty.utah.edu`
- `CORS_ALLOWED_ORIGINS`

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

After deployment, inspect the live backend database coverage with:

```text
GET https://YOUR-RAILWAY-API-DOMAIN/diagnostics/summary
```

If the `total_by_school` or `eligible_by_school` breakdowns show only one school, run a larger backfill instead of tuning ranking first.
