"""Environment configuration. Everything secret comes from env vars only."""
import os

from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# Both defaults are free, vision-capable models on OpenRouter, chosen from two
# different providers on purpose: the free tier is rate limited per model, so a
# fallback on the same provider would hit the same wall. Verify the exact slugs
# on https://openrouter.ai/models before deploying, since free IDs change.
MODEL = os.environ.get("VISFIX_MODEL", "google/gemma-4-26b-a4b-it:free")
FALLBACK_MODEL = os.environ.get("VISFIX_FALLBACK_MODEL", "nvidia/nemotron-nano-12b-v2-vl:free")

# De-duplicated, blank-stripped. OpenRouter reads this array and automatically
# falls back to the next model when one errors or is rate limited.
MODELS = list(dict.fromkeys(m for m in (MODEL, FALLBACK_MODEL) if m))

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_PROMPT_CHARS = 2000
MAX_TOOL_ITERATIONS = 5
RATE_LIMIT = os.environ.get("VISFIX_RATE_LIMIT", "5/15 minutes")


def validate() -> None:
    """Fail loudly at boot instead of silently on the first request."""
    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Copy .env.example to .env or set it in the environment."
        )
    if not MODELS:
        raise RuntimeError("No model configured. Set VISFIX_MODEL.")
