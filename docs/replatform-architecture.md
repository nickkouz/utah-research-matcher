# Replatform Architecture

The project is moving from a demo-era static frontend + lightweight Python function into a production-oriented monorepo:

- `apps/web`: Next.js frontend for the company search, results page, and researcher detail page
- `apps/api`: FastAPI backend for company interpretation, matching, and researcher detail APIs
- `workers/`: offline ingestion and enrichment jobs for Utah profiles, OpenAlex, summaries, and embeddings
- `shared/`: shared contracts and taxonomies

Core infrastructure choices:

- `Postgres + pgvector` for metadata and vector search
- `profiles.faculty.utah.edu` as the researcher identity layer
- `OpenAlex` as the publication and citation metadata layer
- embedding-first retrieval with LLM reranking

Phase 1 only marks researchers with enough publication signal as eligible for matching. The full `profiles.faculty.utah.edu` population should still be ingested into `staff_registry` for later expansion.

