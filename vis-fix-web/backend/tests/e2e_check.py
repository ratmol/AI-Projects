"""End-to-end check against a mock OpenRouter server.

Proves, without spending API credits:
  1. /api/analyze streams SSE: compressed -> status -> tool -> tokens -> done
  2. the agent loop survives MULTIPLE tool-call rounds (the CLI bug)
  3. tool results are fed back to the model correctly
  4. non-images -> 415, oversize -> 413, 6th request in window -> 429

Run:  .venv/Scripts/python tests/e2e_check.py   (from backend/)
"""
import asyncio
import io
import json
import os
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

MOCK_PORT = 9631
os.environ["OPENROUTER_API_KEY"] = "test-key"
os.environ["OPENROUTER_BASE_URL"] = f"http://127.0.0.1:{MOCK_PORT}/v1"
os.environ.pop("TAVILY_API_KEY", None)  # exercises the graceful no-search path

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from PIL import Image

from app.main import app  # noqa: E402  (env must be set before this import)

# ---------- mock OpenRouter ----------
mock = FastAPI()
calls: list[dict] = []

ANSWER_PARTS = ["Here is ", "the **fix**:\n", "```bash\npip install pydantic-settings\n```"]


def _chunk(delta: dict, finish: str | None = None) -> dict:
    return {
        "id": "mock", "object": "chat.completion.chunk", "created": 0, "model": "mock",
        "choices": [{"index": 0, "delta": delta, "finish_reason": finish}],
    }


def _tool_round(call_id: str, query: str) -> list[dict]:
    return [
        _chunk({"role": "assistant", "tool_calls": [{"index": 0, "id": call_id, "type": "function",
                                                     "function": {"name": "web_search", "arguments": ""}}]}),
        _chunk({"tool_calls": [{"index": 0, "function": {"arguments": json.dumps({"query": query})}}]}),
        _chunk({}, finish="tool_calls"),
    ]


@mock.post("/v1/chat/completions")
async def completions(body: dict):
    calls.append(body)
    if len(calls) == 1:
        chunks = _tool_round("call_1", "pydantic BaseSettings moved v2")
    elif len(calls) == 2:
        chunks = _tool_round("call_2", "pydantic-settings migration")
    else:
        chunks = [_chunk({"role": "assistant"})] + [_chunk({"content": p}) for p in ANSWER_PARTS] + [_chunk({}, "stop")]

    async def sse():
        for c in chunks:
            yield f"data: {json.dumps(c)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(sse(), media_type="text/event-stream")


# ---------- helpers ----------
def png_bytes(size=(1400, 900)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, (20, 20, 20)).save(buf, format="PNG")
    return buf.getvalue()


def parse_sse(text: str) -> list[tuple[str, dict]]:
    events = []
    for frame in text.split("\n\n"):
        event, data = None, ""
        for line in frame.split("\n"):
            if line.startswith("event: "):
                event = line[7:]
            elif line.startswith("data: "):
                data += line[6:]
        if event and data:
            events.append((event, json.loads(data)))
    return events


async def run_checks() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1) happy path with two tool rounds
        res = await client.post("/api/analyze", files={"file": ("shot.png", png_bytes(), "image/png")},
                                data={"prompt": "it broke"}, timeout=30)
        assert res.status_code == 200, res.text
        events = parse_sse(res.text)
        names = [e for e, _ in events]
        assert names[0] == "compressed" and names[1] == "status", names
        tool_events = [d for e, d in events if e == "tool"]
        assert len(tool_events) == 2, f"expected 2 tool rounds, got {len(tool_events)}"
        assert tool_events[0]["query"] == "pydantic BaseSettings moved v2"
        answer = "".join(d["text"] for e, d in events if e == "token")
        assert answer == "".join(ANSWER_PARTS), answer
        assert names[-1] == "done", names
        # the model got the tool results back, in order
        assert len(calls) == 3
        tool_msgs = [m for m in calls[2]["messages"] if m["role"] == "tool"]
        assert [m["tool_call_id"] for m in tool_msgs] == ["call_1", "call_2"]
        # image was compressed to fit 1024px
        compressed = events[0][1]
        assert max(compressed["width"], compressed["height"]) <= 1024, compressed
        print("ok: agent loop with 2 tool rounds, streaming, compression")

        # 2) not an image -> 415
        res = await client.post("/api/analyze", files={"file": ("x.png", b"not an image", "image/png")})
        assert res.status_code == 415, res.status_code
        # 3) oversize -> 413
        res = await client.post("/api/analyze", files={"file": ("x.png", b"\0" * (5 * 1024 * 1024 + 1), "image/png")})
        assert res.status_code == 413, res.status_code
        # 4) pixel bomb: small file, 100MP when decoded -> 413, not a 500
        bomb = io.BytesIO()
        Image.new("L", (10000, 10000), 0).save(bomb, format="PNG")
        assert bomb.tell() <= 5 * 1024 * 1024
        res = await client.post("/api/analyze", files={"file": ("bomb.png", bomb.getvalue(), "image/png")})
        assert res.status_code == 413, res.status_code
        print("ok: 415 on non-image, 413 on >5MB and on pixel bomb")

        # 5-6) rate limit: request 5 allowed, 6th -> 429
        for expected in (415, 429):
            res = await client.post("/api/analyze", files={"file": ("x.png", b"junk", "image/png")})
            assert res.status_code == expected, (expected, res.status_code)
        print("ok: 429 after 5 requests per window")


if __name__ == "__main__":
    server = uvicorn.Server(uvicorn.Config(mock, host="127.0.0.1", port=MOCK_PORT, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    deadline = time.time() + 10
    while not server.started:
        if time.time() > deadline:
            raise SystemExit("mock server failed to start")
        time.sleep(0.05)

    asyncio.run(run_checks())
    server.should_exit = True
    print("ALL CHECKS PASSED")
