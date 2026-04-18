from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from openai import OpenAI

from app.core.config import settings


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI | None:
    if not settings.openai_api_key:
        return None
    return OpenAI(api_key=settings.openai_api_key, max_retries=0)


def has_openai_client() -> bool:
    return get_openai_client() is not None


def embed_text(text: str) -> list[float]:
    if not text.strip():
        return []
    client = get_openai_client()
    if client is None:
        return []
    try:
        response = client.embeddings.create(model=settings.openai_embedding_model, input=text)
        return list(response.data[0].embedding)
    except Exception:
        return []


def embed_texts(texts: list[str]) -> list[list[float]]:
    cleaned = [text for text in texts if text.strip()]
    if not cleaned:
        return [[] for _ in texts]
    client = get_openai_client()
    if client is None:
        return [[] for _ in texts]
    try:
        response = client.embeddings.create(model=settings.openai_embedding_model, input=cleaned)
        embedded = [list(item.embedding) for item in response.data]
    except Exception:
        return [[] for _ in texts]
    output: list[list[float]] = []
    pointer = 0
    for text in texts:
        if text.strip():
            output.append(embedded[pointer])
            pointer += 1
        else:
            output.append([])
    return output


def generate_structured_json(
    system_prompt: str,
    user_prompt: str,
    schema_name: str,
    json_schema: dict[str, Any],
    temperature: float = 0.1,
) -> dict[str, Any] | None:
    client = get_openai_client()
    if client is None:
        return None

    try:
        response = client.chat.completions.create(
            model=settings.openai_generation_model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": json_schema,
                },
            },
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)
    except Exception:
        return None
