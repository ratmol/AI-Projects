"""Environment configuration. Everything secret comes from env vars only."""
import os

from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# All defaults are free, vision-capable models on OpenRouter. They are ordered
# primary first, and picked to spread across providers on purpose: the free tier
# is rate limited per model, so a same-provider fallback would hit the same wall.
# Every model here must accept image input, and paid models work too. Verify the
# exact slugs on https://openrouter.ai/models before deploying, since free IDs
# change. Override the whole chain with VISFIX_MODELS (comma separated).
DEFAULT_MODELS = [
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-nano-12b-v2-vl:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
]

# De-duplicated, blank-stripped, order preserved. OpenRouter reads this array
# and automatically falls back to the next model when one errors or is rate
# limited. None of these should ever bill: if all free tiers are exhausted the
# request fails cleanly rather than routing to a paid model.
_configured = os.environ.get("VISFIX_MODELS", "").split(",") or []
MODELS = list(dict.fromkeys(m.strip() for m in _configured if m.strip())) or DEFAULT_MODELS
MODEL = MODELS[0]

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
