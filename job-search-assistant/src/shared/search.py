"""Web search via Tavily API."""
import os
from dataclasses import dataclass
import httpx
from .logger import logger


@dataclass
class TavilyResult:
    title: str
    url: str
    content: str
    score: float


async def web_search(query: str, max_results: int = 5) -> list[TavilyResult]:
    """Search the web using Tavily."""
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("Missing TAVILY_API_KEY")

    logger.debug(f'Tool call: web_search("{query}")')

    async with httpx.AsyncClient() as client:
        res = await client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
            },
        )

    if res.status_code != 200:
        logger.error(f"Tavily search failed: {res.status_code}")
        return []

    data = res.json()
    results = [
        TavilyResult(
            title=r.get("title", ""),
            url=r.get("url", ""),
            content=r.get("content", ""),
            score=r.get("score", 0.0),
        )
        for r in data.get("results", [])
    ]
    logger.debug(f"Search returned {len(results)} results, top: {results[0].url if results else 'none'}")
    return results
