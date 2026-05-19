"""LLM client using OpenAI SDK pointed at OpenRouter."""
import json
import os
from typing import TypeVar, Any
from openai import OpenAI
from .logger import logger

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY") or (_ for _ in ()).throw(ValueError("Missing OPENROUTER_API_KEY")),
)

MODEL = "google/gemini-2.0-flash-001"

T = TypeVar("T")


def _get_client() -> OpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("Missing OPENROUTER_API_KEY")
    return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)


async def chat_json(system_prompt: str, user_prompt: str, retries: int = 2) -> Any:
    """Call LLM and parse JSON response."""
    import asyncio
    llm = _get_client()
    for attempt in range(retries + 1):
        try:
            logger.debug(f"LLM call: {MODEL} (attempt {attempt + 1})")
            res = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: llm.chat.completions.create(
                    model=MODEL,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                ),
            )
            text = res.choices[0].message.content or ""
            logger.debug(f"LLM tokens used: {res.usage.total_tokens if res.usage else 'unknown'}")
            return json.loads(text)
        except Exception as err:
            logger.error(f"LLM attempt {attempt + 1} failed: {err}")
            if attempt == retries:
                raise
    raise RuntimeError("LLM call failed after retries")


async def chat_text(system_prompt: str, user_prompt: str) -> str:
    """Call LLM and return plain text response."""
    import asyncio
    llm = _get_client()
    logger.debug(f"LLM text call: {MODEL}")
    res = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: llm.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        ),
    )
    return res.choices[0].message.content or ""
