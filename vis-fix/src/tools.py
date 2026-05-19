"""Tool definitions and web search implementation."""
import os
import sys
import httpx

# OpenAI-compatible tool schema
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
    """Run a Tavily web search and return formatted results."""
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY is not set in your .env file")

    sys.stderr.write(f'[DEBUG] Running web search for: "{query}"\n')

    async with httpx.AsyncClient() as client:
        res = await client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "max_results": 5,
                "search_depth": "advanced",
            },
        )
        res.raise_for_status()
        data = res.json()

    results = data.get("results", [])
    formatted = "\n\n---\n\n".join(
        f"[{i+1}] {r['title']}\nURL: {r['url']}\n{r['content']}"
        for i, r in enumerate(results)
    )

    sys.stderr.write(f"[DEBUG] Found {len(results)} results\n")
    return formatted
