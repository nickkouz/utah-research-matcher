# Pipeline Contracts

This file defines the canonical JSON contracts for the Utah Research Matcher pipeline. The goal is to let the faculty-dataset workflow and the student-matching workflow evolve independently while keeping a stable interface.

## Stage 0: Raw student input

Input source:
- dashboard form submission

Contract:

```json
{
  "name": "Maya Patel",
  "email": "u1234567@utah.edu",
  "major": "Computer Science",
  "year": "Junior",
  "courses": ["CS 5350 Machine Learning", "CS 5340 NLP"],
  "skills": ["Python", "PyTorch", "scikit-learn"],
  "primary_interest_text": "I want to work on machine learning and language models for clinical text in healthcare.",
  "interests_freetext": "I want to work on machine learning and language models for clinical text in healthcare.",
  "application_areas": ["Healthcare"],
  "methods": ["Machine Learning", "Natural Language Processing"],
  "checkbox_areas": ["Healthcare", "Machine Learning", "Natural Language Processing"],
  "reference_examples": "CS 5350 final project on clinical note classification",
  "goal": "Research experience before applying to PhD programs",
  "commitment_hours": 10,
  "followup_answer": ""
}
```

Rules:
- `courses`, `skills`, `application_areas`, `methods`, and `checkbox_areas` should always be arrays when possible.
- `followup_answer` is optional and only used after the system asks for one more detail.
- Legacy clients may still send only `interests_freetext` and `checkbox_areas`; the normalizer must continue to support that.

## Stage 1: Normalized student profile

Producer:
- `pipeline/normalizer.py`

Contract:

```json
{
  "structured_facts": {
    "name": "Maya Patel",
    "email": "u1234567@utah.edu",
    "major": "Computer Science",
    "year": "Junior",
    "courses": ["CS 5350 Machine Learning", "CS 5340 NLP"],
    "skills": ["Python", "PyTorch", "scikit-learn"],
    "time_commitment_hours": 10,
    "checkbox_areas": ["Healthcare", "Machine Learning", "Natural Language Processing"],
    "application_areas": ["Healthcare"],
    "methods": ["Machine Learning", "Natural Language Processing"],
    "reference_examples": ["CS 5350 final project on clinical note classification"]
  },
  "research_summary": "Undergraduate in Computer Science seeking research experience in machine learning and language models for healthcare and clinical text. Methods of interest include Machine Learning and Natural Language Processing.",
  "research_methods": ["Machine Learning", "Natural Language Processing"],
  "application_domains": ["Healthcare"],
  "interest_keywords": ["machine learning", "language models", "clinical text", "healthcare"],
  "experience_signals": ["CS 5350 Machine Learning", "Python", "PyTorch"],
  "confidence": "high",
  "needs_followup": false,
  "followup_question": ""
}
```

Rules:
- `structured_facts` contains cleaned factual fields only.
- `research_summary` is the primary embedding text for student retrieval.
- `research_methods`, `application_domains`, and `interest_keywords` should be grounded in the student’s actual inputs or explicit selections.
- `confidence` must be one of `high`, `medium`, or `low`.
- `needs_followup` and `followup_question` are required, even if `needs_followup` is false.

## Stage 1b: Follow-up response

Producer:
- `pipeline/orchestrator.py`

Contract when the student profile is too vague:

```json
{
  "status": "needs_followup",
  "student": { "... normalized student profile ..." },
  "matches": [],
  "followup_question": "What methods or technical approaches are you most interested in, such as machine learning, NLP, computer vision, HCI, systems, or security?",
  "reason": "Student interests are still too broad for confident faculty matching."
}
```

Rules:
- The frontend should show the question inline on the form and resubmit with `followup_answer`.
- Matching should not proceed until the follow-up answer is provided or the profile becomes specific enough.

## Stage 2: Faculty dataset load

Producer:
- `data/faculty_db.json` from the faculty-dataset workflow

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
    "normalized_research_summary": "Research interests include natural language processing and machine learning for clinical text.",
    "research_keywords": ["natural language processing", "machine learning", "clinical text"],
    "paper_titles_text": "Structured prediction with clinical reasoning",
    "embedding_summary": [0.1, 0.2, 0.3],
    "embedding_papers": [0.05, 0.1, 0.2],
    "browser_snippet": "Natural language processing and machine learning for clinical text.",
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
- `normalized_research_summary`
- `research_keywords`
- `paper_titles_text`
- `embedding_summary`
- `embedding_papers`
- `browser_snippet`
- `last_active_year`
- `accepts_undergrads`

Rules:
- All scraped faculty may appear in browsing.
- Records with weak signal may still exist in the dataset but can be marked ineligible for top-match recommendation by the normalization/ranking layer.

## Stage 2b: Faculty browser payload

Producer:
- `pipeline/build_browser_payload.py`

Contract:

```json
[
  {
    "id": "srikumar_vivek",
    "name": "Vivek Srikumar",
    "title": "Associate Professor",
    "department": "Kahlert School of Computing",
    "browser_snippet": "Natural language processing and machine learning for clinical text.",
    "profile_url": "https://example.com/profile",
    "last_active_year": 2024,
    "research_keywords": ["natural language processing", "machine learning", "clinical text"],
    "accepts_undergrads": null,
    "eligible_for_matching": true
  }
]
```

Rules:
- This payload is browse-safe and intentionally lighter than the full faculty record.
- The homepage should use this payload only for browsing, not for ranking.

## Stage 3: Ranked matches

Producer:
- `pipeline/ranker.py`

Contract:

```json
[
  {
    "faculty": { "... normalized faculty record ..." },
    "score": 0.68,
    "overlap_terms": ["machine learning", "clinical text"],
    "component_scores": {
      "summary_similarity": 0.74,
      "facet_similarity": 0.52,
      "keyword_overlap": 0.44,
      "recency": 1.0,
      "undergrad_friendliness": 0.5
    },
    "match_strength": "strong",
    "warning": null,
    "rerank_notes": ""
  }
]
```

Rules:
- Candidate generation should score summary similarity, facet similarity, keyword overlap, recency, and undergrad-friendliness.
- Top candidates may then be reranked by an LLM and diversity-adjusted before the final top 5 is returned.
- `match_strength` must be one of `strong`, `good`, or `possible`.

## Stage 4: Match rationale generation

Producer:
- `pipeline/rationale.py`

Contract:

```json
{
  "faculty_id": "srikumar_vivek",
  "rationale": "This faculty member is a strong fit because their work in natural language processing and clinical text aligns with the student's stated interest in machine learning for healthcare."
}
```

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

## Stage 7: Final student-facing results object

Producer:
- `pipeline/orchestrator.py`

Contract:

```json
{
  "status": "ready",
  "student": { "... normalized student profile ..." },
  "matches": [
    {
      "faculty": { "... normalized faculty record ..." },
      "score": 0.68,
      "match_strength": "strong",
      "warning": null,
      "rationale": "This faculty member is a strong fit because ...",
      "emails": {
        "coffee_chat": { "subject": "...", "body": "...", "faculty_email": "..." },
        "lab_inquiry": { "subject": "...", "body": "...", "faculty_email": "..." },
        "paper_response": { "subject": "...", "body": "...", "faculty_email": "..." }
      }
    }
  ]
}
```

Rules:
- This is the only object the results page should need.
- The frontend should not recompute ranking, retrieval, or email structures.
- `matches` should already be filtered, ranked, and presentation-ready.
