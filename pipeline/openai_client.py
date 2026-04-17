from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - handled by runtime environment
    def load_dotenv() -> bool:
        return False

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - handled by runtime environment
    OpenAI = None  # type: ignore[assignment]


EMBEDDING_MODEL = "text-embedding-3-small"
GENERATION_MODEL = os.getenv("OPENAI_GENERATION_MODEL", "gpt-4o-mini")


load_dotenv()


@lru_cache(maxsize=1)
def get_openai_client() -> Any | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None
    return OpenAI(api_key=api_key)


def has_openai_client() -> bool:
    return get_openai_client() is not None


def embed_text(text: str, model: str = EMBEDDING_MODEL) -> list[float]:
    client = get_openai_client()
    if client is None:
        return []

    response = client.embeddings.create(model=model, input=text)
    return list(response.data[0].embedding)


def generate_json(
    system_prompt: str,
    user_prompt: str,
    model: str = GENERATION_MODEL,
) -> dict[str, Any] | None:
    client = get_openai_client()
    if client is None:
        return None

    try:
        response = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content or "{}"
        import json

        return json.loads(content)
    except Exception:
        return None
