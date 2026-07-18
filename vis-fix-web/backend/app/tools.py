"""Tool definitions and web search implementation (Tavily)."""
import logging

import httpx

from . import settings

logger = logging.getLogger(__name__)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Searches the web for technical documentation, coding errors, and other details to help with debugging.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to use based on the screenshot",
                    }
                },
                "required": ["query"],
            },
        },
    }
]


async def run_web_search(query: str) -> str:
    """Run a Tavily web search and return formatted results.

    Failures are reported back to the model as text instead of raised, so
    one flaky search doesn't kill the whole analysis.
    """
    if not settings.TAVILY_API_KEY:
        return (
            "Web search is unavailable (not configured). Answer from your own "
            "knowledge and mention that the fix was not verified against current docs."
        )

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            res = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": settings.TAVILY_API_KEY,
                    "query": query,
                    "max_results": 5,
                    "search_depth": "advanced",
                },
            )
            res.raise_for_status()
            data = res.json()
    except httpx.HTTPError as exc:
        logger.warning("Tavily search failed: %r", exc)
        return f"Web search failed ({type(exc).__name__}). Answer from your own knowledge."

    results = data.get("results", [])
    if not results:
        return "No search results found."

    return "\n\n---\n\n".join(
        f"[{i + 1}] {r['title']}\nURL: {r['url']}\n{r['content']}"
        for i, r in enumerate(results)
    )
