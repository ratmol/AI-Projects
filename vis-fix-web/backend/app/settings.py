"""Environment configuration. Everything secret comes from env vars only."""
import os

from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
MODEL = os.environ.get("VISFIX_MODEL", "google/gemini-3-flash-preview")

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
