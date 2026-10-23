"""Gemini (Vertex AI) helpers with retries. All model names come from settings."""
import asyncio
import json
import logging
import re

from google import genai
from google.genai import types

from ..config import settings

log = logging.getLogger("llm")
client = genai.Client(vertexai=True, project=settings.GCP_PROJECT, location=settings.VERTEX_LOCATION)
_thinking_unsupported: set[str] = set()


def thinking_config(model: str, budget: int | None):
    if budget is None or budget < 0 or model in _thinking_unsupported:
        return None
    return types.ThinkingConfig(thinking_budget=budget)


def mark_thinking_unsupported(model: str, err: Exception) -> bool:
    if "thinking" in str(err).lower() and model not in _thinking_unsupported:
        _thinking_unsupported.add(model)
        log.warning("thinking config not supported by %s; disabling", model)
        return True
    return False


def _transient(e: Exception) -> bool:
    s = str(e)
    return any(x in s for x in ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE", "500", "INTERNAL", "deadline", "timed out"))


def parse_json(text: str):
    text = (text or "").strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if m:
        text = m.group(1)
    return json.loads(text)


async def gen_json(prompt: str, schema: dict, model: str | None = None, temperature: float = 0.2,
                   system: str | None = None, thinking: int | None = 0) -> dict:
    model = model or settings.GEMINI_FAST_MODEL
    last = None
    for attempt in range(3):
        cfg = types.GenerateContentConfig(
            temperature=temperature, response_mime_type="application/json", response_schema=schema,
            system_instruction=system,
            thinking_config=thinking_config(model, thinking if "pro" not in model else None))
        try:
            resp = await client.aio.models.generate_content(model=model, contents=prompt, config=cfg)
            return parse_json(resp.text)
        except Exception as e:  # noqa
            last = e
            if mark_thinking_unsupported(model, e):
                continue
            if isinstance(e, json.JSONDecodeError) or _transient(e):
                await asyncio.sleep(0.5 * (2 ** attempt))
                continue
            break
    raise RuntimeError(f"LLM JSON generation failed: {last}")


async def embed(text: str) -> list[float]:
    resp = await client.aio.models.embed_content(
        model=settings.GEMINI_EMBED_MODEL, contents=[(text or " ")[:6000]],
        config=types.EmbedContentConfig(output_dimensionality=settings.EMBED_DIM))
    return list(resp.embeddings[0].values)
