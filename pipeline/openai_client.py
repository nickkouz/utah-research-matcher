from __future__ import annotations

import json
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
GENERATION_MODEL = os.getenv("OPENAI_GENERATION_MODEL", "gpt-5-mini")


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
    if not text.strip():
        return []
    client = get_openai_client()
    if client is None:
        return []

    response = client.embeddings.create(model=model, input=text)
    return list(response.data[0].embedding)


def embed_texts(texts: list[str], model: str = EMBEDDING_MODEL) -> list[list[float]]:
    cleaned_inputs = [text for text in texts if text.strip()]
    if not cleaned_inputs:
        return []

    client = get_openai_client()
    if client is None:
        return [[] for _ in texts]

    response = client.embeddings.create(model=model, input=cleaned_inputs)
    embeddings = [list(item.embedding) for item in response.data]

    output: list[list[float]] = []
    embedding_index = 0
    for text in texts:
        if text.strip():
            output.append(embeddings[embedding_index])
            embedding_index += 1
        else:
            output.append([])
    return output


def generate_structured_json(
    system_prompt: str,
    user_prompt: str,
    schema_name: str,
    json_schema: dict[str, Any],
    model: str = GENERATION_MODEL,
    temperature: float = 0.1,
) -> dict[str, Any] | None:
    client = get_openai_client()
    if client is None:
        return None

    try:
        response = client.chat.completions.create(
            model=model,
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
        return generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            temperature=temperature,
        )


def generate_json(
    system_prompt: str,
    user_prompt: str,
    model: str = GENERATION_MODEL,
    temperature: float = 0.2,
) -> dict[str, Any] | None:
    client = get_openai_client()
    if client is None:
        return None

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)
    except Exception:
        return None
