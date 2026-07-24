"""The agent loop, streamed as (event, payload) tuples.

Replaces the CLI's single-shot tool handling: the model can chain multiple
web searches before answering. Capped at MAX_TOOL_ITERATIONS to bound cost;
after the cap one last call runs with tools disabled so the user always
gets an answer instead of a dangling tool request.
"""
import json
import logging
from typing import AsyncGenerator

from openai import AsyncOpenAI, OpenAIError

from . import settings
from .system_prompt import SYSTEM_PROMPT
from .tools import TOOLS, run_web_search

logger = logging.getLogger(__name__)

Event = tuple[str, dict]


async def run_analysis(image_b64: str, mime: str, user_prompt: str) -> AsyncGenerator[Event, None]:
    client = AsyncOpenAI(
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.OPENROUTER_BASE_URL,
    )
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_b64}"}},
            ],
        },
    ]

    yield "status", {"stage": "analyzing"}

    try:
        for iteration in range(settings.MAX_TOOL_ITERATIONS + 1):
            # tools stays in every request (the history references them);
            # tool_choice="none" is what actually forces the final answer.
            allow_tools = iteration < settings.MAX_TOOL_ITERATIONS
            # `model` is the primary; OpenRouter's `models` array is what makes
            # it fall back to the next one on error or rate limit.
            stream = await client.chat.completions.create(
                model=settings.MODEL,
                max_tokens=2048,
                messages=messages,
                stream=True,
                tools=TOOLS,
                tool_choice="auto" if allow_tools else "none",
                extra_body={"models": settings.MODELS} if len(settings.MODELS) > 1 else {},
            )

            # Streaming splits tool calls into deltas keyed by index;
            # reassemble id/name/arguments before executing anything.
            content_parts: list[str] = []
            tool_calls: dict[int, dict] = {}
            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta.content:
                    content_parts.append(delta.content)
                    yield "token", {"text": delta.content}
                for tc in delta.tool_calls or []:
                    slot = tool_calls.setdefault(tc.index, {"id": "", "name": "", "arguments": ""})
                    if tc.id:
                        slot["id"] = tc.id
                    if tc.function:
                        slot["name"] += tc.function.name or ""
                        slot["arguments"] += tc.function.arguments or ""

            if not tool_calls:
                if content_parts:
                    yield "done", {}
                else:
                    yield "error", {"message": "The model returned an empty response. Please try again."}
                return

            ordered = [tool_calls[i] for i in sorted(tool_calls)]
            messages.append(
                {
                    "role": "assistant",
                    "content": "".join(content_parts) or None,
                    "tool_calls": [
                        {
                            "id": call["id"],
                            "type": "function",
                            "function": {"name": call["name"], "arguments": call["arguments"]},
                        }
                        for call in ordered
                    ],
                }
            )

            for call in ordered:
                if call["name"] == "web_search":
                    try:
                        query = json.loads(call["arguments"]).get("query", "")
                    except json.JSONDecodeError:
                        query = ""
                    yield "tool", {"name": "web_search", "query": query}
                    result = await run_web_search(query) if query else "Invalid web_search arguments."
                else:
                    result = f"Unknown tool: {call['name']}"
                messages.append({"role": "tool", "tool_call_id": call["id"], "content": result})

        yield "error", {"message": "The model did not produce a final answer. Please try again."}
    except OpenAIError as exc:
        logger.error("Model call failed: %r", exc)
        yield "error", {"message": "The AI service is unavailable right now. Please try again in a minute."}
