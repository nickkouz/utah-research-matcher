# Pipeline Contracts

This file defines the stage-by-stage JSON contracts for the Utah Research Matcher pipeline. The goal is to let the pipeline owner and the staff-database owner work independently while preserving a stable integration surface.

## Stage 0: Raw student input

Input source:
- frontend form submission

Contract:

```json
{
  "name": "Maya Patel",
  "email": "u1234567@utah.edu",
  "major": "Computer Science",
  "year": "Junior",
  "courses": ["CS 5350 Machine Learning", "CS 5340 NLP"],
  "skills": ["Python", "PyTorch", "scikit-learn"],
  "interests_freetext": "I want to use machine learning and language models for healthcare and clinical text.",
  "checkbox_areas": ["Machine Learning", "Healthcare", "Natural Language Processing"],
  "goal": "Research experience before applying to PhD programs",
  "commitment_hours": 10
}
```

Rules:
- `courses`, `skills`, and `checkbox_areas` should always be arrays, even if empty.
- `commitment_hours` should be numeric.
- Missing or blank values may be passed through and handled during normalization.

## Stage 1: Normalized student profile

Producer:
- `pipeline/normalizer.py`

Contract:

```json
{
  "structured_facts": {
    "name": "Maya Patel",
    "major": "Computer Science",
    "year": "Junior",
    "courses": ["CS 5350 Machine Learning", "CS 5340 NLP"],
    "skills": ["Python", "PyTorch", "scikit-learn"],
    "time_commitment_hours": 10,
    "checkbox_areas": ["Machine Learning", "Healthcare", "Natural Language Processing"]
  },
  "research_summary": "Undergraduate in Computer Science seeking research experience in machine learning and language models for healthcare and clinical text.",
  "confidence": "high"
}
```

Rules:
- `structured_facts` must contain cleaned factual fields only.
- `research_summary` is the text used for embedding and matching.
- `confidence` must be one of `high`, `medium`, or `low`.
- No invented interests or inflated skill claims.

## Stage 2: Faculty dataset load

Producer:
- `data/faculty_db.json` from the staff-database workflow

Contract:

```json
[
  {
    "id": "srikumar_vivek",
    "name": "Vivek Srikumar",
    "title": "Associate Professor",
    "department": "Kahlert School of Computing",
    "email": "svivek@cs.utah.edu",
    "profile_url": "https://example.com/profile",
    "bio": "Research interests include natural language processing and machine learning for clinical text.",
    "recent_papers": [
      {
        "title": "Structured prediction with clinical reasoning",
        "year": 2024,
        "venue": "ACL 2024",
        "url": "https://example.com/paper"
      }
    ],
    "research_text": "natural language processing machine learning clinical text structured prediction",
    "embedding": [0.1, 0.2, 0.3],
    "last_active_year": 2024,
    "accepts_undergrads": null
  }
]
```

Required fields per faculty record:
- `id`
- `name`
- `title`
- `department`
- `email`
- `profile_url`
- `bio`
- `recent_papers`
- `research_text`
- `embedding`
- `last_active_year`
- `accepts_undergrads`

Rules:
- `recent_papers` must always be an array.
- `embedding` may be an empty array during fallback or pre-embedding stages.
- `research_text` should be the canonical text source for ranking.

## Stage 3: Ranked matches

Producer:
- `pipeline/ranker.py`

Contract:

```json
[
  {
    "faculty": {
      "id": "srikumar_vivek",
      "name": "Vivek Srikumar",
      "title": "Associate Professor",
      "department": "Kahlert School of Computing",
      "email": "svivek@cs.utah.edu",
      "profile_url": "https://example.com/profile",
      "bio": "Research interests include natural language processing and machine learning for clinical text.",
      "recent_papers": [],
      "research_text": "natural language processing machine learning clinical text",
      "embedding": [],
      "last_active_year": 2024,
      "accepts_undergrads": null
    },
    "score": 0.89,
    "overlap_terms": ["machine", "learning", "clinical", "text"],
    "match_strength": "strong",
    "warning": null
  }
]
```

Rules:
- Output must be sorted best-to-worst.
- Return exactly 5 matches when 5 or more faculty are available.
- `score` should be numeric.
- `match_strength` should be one of `strong`, `good`, or `possible`.
- `warning` is nullable and used for stale or weak records.

## Stage 4: Match rationale generation

Producer:
- `pipeline/rationale.py` or rationale logic inside `pipeline/emailer.py`

Contract:

```json
{
  "faculty_id": "srikumar_vivek",
  "rationale": "This faculty member is a strong fit because their recent work in natural language processing and clinical text aligns with the student's stated interests in machine learning for healthcare and language models."
}
```

Rules:
- Ground the explanation in student interests and faculty research only.
- Do not claim the faculty is actively recruiting unless the dataset says so.
- Keep it concise and specific enough for a card UI.

## Stage 5: Email generation

Producer:
- `pipeline/emailer.py`

Contract:

```json
{
  "faculty_id": "srikumar_vivek",
  "emails": {
    "coffee_chat": {
      "subject": "Undergraduate interested in your research",
      "body": "Dear Professor Srikumar,\n\n...",
      "faculty_email": "svivek@cs.utah.edu"
    },
    "lab_inquiry": {
      "subject": "Question about undergraduate research opportunities",
      "body": "Dear Professor Srikumar,\n\n...",
      "faculty_email": "svivek@cs.utah.edu"
    },
    "paper_response": {
      "subject": "Interested in your recent research direction",
      "body": "Dear Professor Srikumar,\n\n...",
      "faculty_email": "svivek@cs.utah.edu"
    }
  }
}
```

Rules:
- Always include exactly these three email modes.
- `subject`, `body`, and `faculty_email` are required in each mode.
- Emails should be presentable to students without additional cleanup.

## Stage 6: Agent review

Producer:
- `pipeline/critic.py`

Contract:

```json
{
  "faculty_id": "srikumar_vivek",
  "approved": true,
  "issues": [],
  "revised_rationale": null,
  "revised_emails": null
}
```

Alternative when revision is needed:

```json
{
  "faculty_id": "srikumar_vivek",
  "approved": false,
  "issues": [
    "Rationale is too generic.",
    "Lab inquiry email does not mention the student's relevant skills."
  ],
  "revised_rationale": "Updated rationale text here.",
  "revised_emails": {
    "coffee_chat": {
      "subject": "Undergraduate interested in your research",
      "body": "Revised body here.",
      "faculty_email": "svivek@cs.utah.edu"
    },
    "lab_inquiry": {
      "subject": "Question about undergraduate research opportunities",
      "body": "Revised body here.",
      "faculty_email": "svivek@cs.utah.edu"
    },
    "paper_response": {
      "subject": "Interested in your recent research direction",
      "body": "Revised body here.",
      "faculty_email": "svivek@cs.utah.edu"
    }
  }
}
```

Rules:
- One review object per ranked match.
- Revisions are optional and nullable.
- The orchestrator decides whether to use original or revised content.

## Stage 7: Final student-facing results object

Producer:
- `pipeline/orchestrator.py`

Contract:

```json
{
  "student": {
    "structured_facts": {
      "name": "Maya Patel",
      "major": "Computer Science",
      "year": "Junior",
      "courses": ["CS 5350 Machine Learning", "CS 5340 NLP"],
      "skills": ["Python", "PyTorch", "scikit-learn"],
      "time_commitment_hours": 10,
      "checkbox_areas": ["Machine Learning", "Healthcare", "Natural Language Processing"]
    },
    "research_summary": "Undergraduate in Computer Science seeking research experience in machine learning and language models for healthcare and clinical text.",
    "confidence": "high"
  },
  "matches": [
    {
      "faculty": {
        "id": "srikumar_vivek",
        "name": "Vivek Srikumar",
        "title": "Associate Professor",
        "department": "Kahlert School of Computing",
        "email": "svivek@cs.utah.edu",
        "profile_url": "https://example.com/profile",
        "bio": "Research interests include natural language processing and machine learning for clinical text.",
        "recent_papers": [],
        "research_text": "natural language processing machine learning clinical text",
        "embedding": [],
        "last_active_year": 2024,
        "accepts_undergrads": null
      },
      "score": 0.89,
      "match_strength": "strong",
      "warning": null,
      "rationale": "This faculty member is a strong fit because their recent work in natural language processing and clinical text aligns with the student's stated interests.",
      "emails": {
        "coffee_chat": {
          "subject": "Undergraduate interested in your research",
          "body": "Dear Professor Srikumar,\n\n...",
          "faculty_email": "svivek@cs.utah.edu"
        },
        "lab_inquiry": {
          "subject": "Question about undergraduate research opportunities",
          "body": "Dear Professor Srikumar,\n\n...",
          "faculty_email": "svivek@cs.utah.edu"
        },
        "paper_response": {
          "subject": "Interested in your recent research direction",
          "body": "Dear Professor Srikumar,\n\n...",
          "faculty_email": "svivek@cs.utah.edu"
        }
      }
    }
  ]
}
```

Rules:
- This is the only object the frontend should need.
- The frontend should not recompute ranking or derive email structure.
- `matches` should be pre-ranked and presentation-ready.

## Integration rules

- The staff-database owner is responsible for Stage 2 compatibility.
- The pipeline owner is responsible for Stages 1 and 3 through 7.
- If a schema changes, update this file, `AGENTS.md`, and any sample data in the same PR.
