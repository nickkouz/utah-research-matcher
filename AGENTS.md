# AGENTS.md

This file is the context document for AI coding assistants (Codex, Claude) working on this project. Read it before starting any task. Keep it open in a tab while working.

---

## Project summary

**What**: An AI agent that matches undergraduates to faculty research mentors at the University of Utah, and drafts personalized cold emails to those faculty.

**Why**: Utah has 25,000+ undergrads, most of whom do not do research because discovery and outreach are high-friction. This tool compresses that process from weeks to minutes.

**For whom**: Built for the Build with AI Codex Hackathon. Judging rubric weighs impact (25%), Codex usage (25%), creative skill use (25%), demo quality (10%), and feasibility (15%).

---

## Architecture

The system is a linear pipeline with parallelization at the LLM stages:

```text
[Student form]
      |
      v
[Stage 1: Normalize student profile]        (1 LLM call)
      |
      v
[Stage 2: Vagueness check and follow-up]    (0-1 LLM calls, conditional)
      |
      v
[Stage 3: Load pre-built faculty_db.json]   (no LLM, local file)
      |
      v
[Stage 4: Embed student, cosine similarity] (1 embedding call)
      |
      v
[Stage 5: Generate 5 match rationales]      (5 parallel LLM calls)
      |
      v
[Stage 6: Generate 15 emails: 5 faculty x 3 modes]  (15 parallel LLM calls)
      |
      v
[Stage 7: Critic review with 1 revision loop max]   (up to 30 parallel LLM calls)
      |
      v
[Results page: 5 faculty cards with toggleable emails]
```

Pre-hackathon work (done once, not during demo):

```text
[Scrape Utah faculty pages]
      |
      v
[Enrich with recent publications]
      |
      v
[Generate embedding per faculty]
      |
      v
[Save faculty_db.json]
```

---

## Data contracts

These are the canonical schemas. If you change one, update this file and tell the team.

### Faculty record (in `faculty_db.json`)

```json
{
  "id": "srikumar_vivek",
  "name": "Vivek Srikumar",
  "title": "Associate Professor",
  "department": "School of Computing",
  "email": "svivek@cs.utah.edu",
  "profile_url": "https://...",
  "bio": "Research interests include natural language processing, structured prediction, and machine learning for clinical text...",
  "recent_papers": [
    {
      "title": "Structured prediction with clinical reasoning",
      "year": 2024,
      "venue": "ACL 2024",
      "url": "https://arxiv.org/..."
    }
  ],
  "research_text": "concatenated blob of bio + paper titles, used as the embedding source",
  "embedding": [0.023, -0.451, 0.892, "... 1536 floats total ..."],
  "last_active_year": 2024,
  "accepts_undergrads": null
}
```

Fields:
- `id`: slugified `lastname_firstname`, used as the stable key
- `embedding`: from OpenAI `text-embedding-3-small`, length 1536
- `last_active_year`: year of most recent publication, used to flag inactive faculty
- `accepts_undergrads`: boolean or null. Leave null if unsure

### Student input (from the form)

```json
{
  "name": "Maya Patel",
  "email": "u1234567@utah.edu",
  "major": "Computer Science",
  "year": "Junior",
  "courses": ["CS 5350 Machine Learning", "CS 5340 NLP"],
  "skills": ["Python", "PyTorch", "scikit-learn"],
  "interests_freetext": "I'm interested in using AI to help doctors with medical imaging...",
  "checkbox_areas": ["Machine Learning", "Healthcare"],
  "goal": "Research experience before PhD applications",
  "commitment_hours": 10
}
```

### Normalized student profile (output of Stage 1)

```json
{
  "structured_facts": { "... copied from input ..." },
  "research_summary": "Undergraduate CS student interested in machine learning for medical imaging...",
  "confidence": "high"
}
```

### Results object (what the frontend renders)

```json
{
  "student": { "... normalized profile ..." },
  "matches": [
    {
      "faculty": { "... faculty record ..." },
      "score": 0.89,
      "rationale": "Dr. Srikumar's work on clinical NLP...",
      "match_strength": "strong",
      "warning": null,
      "emails": {
        "coffee_chat": { "subject": "...", "body": "...", "faculty_email": "..." },
        "lab_inquiry": { "subject": "...", "body": "...", "faculty_email": "..." },
        "paper_response": { "subject": "...", "body": "...", "faculty_email": "..." }
      }
    }
  ]
}
```

---

## Repo conventions

### Folder structure

```text
/scraper           Faculty scraping scripts / staff database owner
  scraper.py
  enrich_semantic_scholar.py
  build_db.py
/pipeline          AI pipeline / matching owner
  normalizer.py    Stage 1
  vagueness.py     Stage 2
  ranker.py        Stages 3-4
  rationale.py     Stage 5
  emailer.py       Stage 6
  critic.py        Stage 7
  orchestrator.py  Top-level runner
  /prompts
    01_normalizer.md
    02_vagueness.md
    03_rationale.md
    04_emailer.md
    05_critic.md
/frontend          UI and demo shell
  index.html
  results.html
  app.js
  styles.css
/data
  faculty_db.json
  fallback_db.json
  demo_student.json
AGENTS.md
README.md
.env.example
requirements.txt
```

### Team split

For this project, the team has two primary owners:

- Staff database owner: responsible for scraping faculty profiles, structuring records, enriching publication metadata, and keeping the faculty dataset current.
- Pipeline owner: responsible for student normalization, vagueness detection, ranking, rationale generation, email generation, and orchestration.

The pipeline must remain runnable against `data/fallback_db.json` even while the full faculty database is still being built.

### Branch naming

- `main` - always demo-ready; no direct pushes
- `staff-db/*` - faculty scraping and dataset work
- `pipeline/*` - student profile, matching, prompts, and email work
- `integration/*` - merging and glue work
- `demo/*` - demo prep and polish

### Commits and PRs

- Commit frequently, push often
- PR titles should describe what ships, for example `Add critic agent with revision loop`
- No merge to `main` without at least one other person looking at it
- If you are blocked on someone else's work, mock their interface and keep going

### Environment variables

Store in `.env` and never commit it. Example:

```text
OPENAI_API_KEY=sk-...
SEMANTIC_SCHOLAR_API_KEY=...
```

Load with `python-dotenv` on the backend.

---

## LLM conventions

### Models

- Generation: GPT-5-Codex or GPT-5
- Embeddings: `text-embedding-3-small`, dimension 1536

### Structured output

All LLM prompts return JSON. Use structured output or JSON mode. Parse defensively and retry once on malformed responses.

### Parallelization

Stages 5, 6, and 7 should use `asyncio.gather()` or the OpenAI async client. Do not run them sequentially if it can be avoided.

### Prompts

All prompts live in `/pipeline/prompts/` as markdown files. Load them at runtime rather than hardcoding.

---

## Non-goals for this hackathon

- No user accounts, no login, no persistence across sessions
- No auto-sending emails; student copies to clipboard
- No bilingual UI
- No GPA or transcript handling
- No payment flow
- No production-grade deployment required

---

## The Codex story

The hackathon judges 25% on creative use of Codex specifically. Document that story:

- Use Codex to parallelize scraping and pipeline development
- Use a second Codex pass as the critic
- Use Codex for prompt-writing, schema design, and pitch support
- Capture screenshots of parallel work for the demo

---

## Demo plan

Target: 3-minute demo.

1. Problem framing: 25,000 Utah undergrads and high-friction research discovery
2. Show the form being filled out with a real student profile
3. Run the pipeline and show the results cards
4. Open a faculty card and show personalized email options
5. Close with the Codex story and team workflow

Fallback: pre-recorded screen capture if anything breaks.

---

## When in doubt

- Favor working code that is rough over polished code that is broken
- If stuck on a decision, pick the simpler option and keep moving
- The demo is the deliverable
- Push your branch often so teammates can help if you hit a wall

---

## Questions for the team

If you are an AI assistant reading this and a teammate is prompting you: start by reading this file, ask clarifying questions when needed, do not invent features that are not in this doc, and do not change data schemas without flagging it.
