"""End-to-end check against a mock OpenRouter server.

Proves, without spending API credits:
  1. /api/analyze streams SSE: compressed -> status -> tool -> tokens -> done
  2. the agent loop survives MULTIPLE tool-call rounds (the CLI bug)
  3. tool results are fed back to the model correctly
  4. non-images -> 415, oversize -> 413, pixel bomb -> 413, 6th request -> 429

The mock doubles as the local demo backend when no real API key is present.
It picks a scenario from the uploaded image's height, so each bundled example
returns its own realistic answer instead of one canned reply, and it derives
the round from the request itself rather than a global counter, so repeated
runs behave identically.

Run:  .venv/Scripts/python tests/e2e_check.py   (from backend/)
"""
import asyncio
import base64
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

from app import settings  # noqa: E402
from app.main import app  # noqa: E402  (env must be set before this import)

# ---------- mock OpenRouter ----------
mock = FastAPI()
calls: list[dict] = []

PYDANTIC = {
    "queries": ["pydantic BaseSettings moved v2", "pydantic-settings migration guide"],
    "answer": [
        "## What broke\n\n",
        "`BaseSettings` was removed from the main `pydantic` package in **Pydantic v2**. ",
        "It now lives in a separate package called `pydantic-settings`, so the import at ",
        "`main.py` line 4 fails even though Pydantic itself is installed correctly.\n\n",
        "## Fix\n\n",
        "Install the new package:\n\n",
        "```bash\npip install pydantic-settings\n```\n\n",
        "Then update the import:\n\n",
        "```python\n# before\nfrom pydantic import BaseSettings\n\n"
        "# after\nfrom pydantic_settings import BaseSettings\n```\n\n",
        "If you pin dependencies, add it to `requirements.txt` as well:\n\n",
        "```\npydantic>=2.0\npydantic-settings>=2.0\n```\n\n",
        "## Why it happened\n\n",
        "Pydantic v2 split settings management out of the core library to keep the base ",
        "package lighter. Any v1 tutorial will still show the old import, which is why this ",
        "catches people upgrading an existing project.\n\n",
        "## References\n\n",
        "- https://docs.pydantic.dev/latest/migration/\n",
        "- https://docs.pydantic.dev/latest/concepts/pydantic_settings/\n",
    ],
}

NPM_ERESOLVE = {
    "queries": ["react-day-picker 8 date-fns 3 peer dependency ERESOLVE"],
    "answer": [
        "## What broke\n\n",
        "`react-day-picker@8.10.1` declares a peer dependency of `date-fns@^2.28.0`, ",
        "but your project has `date-fns@3.6.0` installed. npm refuses to build a tree ",
        "where a peer requirement cannot be satisfied, so the install aborts with ",
        "`ERESOLVE`.\n\n",
        "## Fix\n\n",
        "The cleanest option is to upgrade the picker, since v9 supports date-fns v3:\n\n",
        "```bash\nnpm install react-day-picker@latest\n```\n\n",
        "If you need to stay on v8, pin date-fns back instead:\n\n",
        "```bash\nnpm install date-fns@^2.30.0\n```\n\n",
        "## What not to do\n\n",
        "`--force` and `--legacy-peer-deps` will make the error go away without fixing ",
        "the mismatch. The picker will then call date-fns functions whose signatures ",
        "changed in v3, and you get a runtime error instead of an install error. Use them ",
        "only as a temporary unblock.\n\n",
        "## References\n\n",
        "- https://daypicker.dev/upgrading\n",
        "- https://docs.npmjs.com/cli/v10/commands/npm-install\n",
    ],
}

CORS = {
    "queries": ["FastAPI CORSMiddleware allow_origins localhost vite"],
    "answer": [
        "## What broke\n\n",
        "This is a server configuration problem, not a bug in your fetch call. The browser ",
        "sent the request from `http://localhost:5173`, and the API at `http://localhost:8000` ",
        "replied without an `Access-Control-Allow-Origin` header, so the browser discarded ",
        "the response.\n\n",
        "The `200 (OK)` in the console is misleading: the server answered fine, the browser ",
        "just refused to hand the result to your JavaScript.\n\n",
        "## Fix\n\n",
        "Add CORS middleware on the API. For FastAPI:\n\n",
        "```python\nfrom fastapi.middleware.cors import CORSMiddleware\n\n"
        "app.add_middleware(\n"
        "    CORSMiddleware,\n"
        '    allow_origins=["http://localhost:5173"],\n'
        "    allow_credentials=True,\n"
        '    allow_methods=["*"],\n'
        '    allow_headers=["*"],\n'
        ")\n```\n\n",
        "Restart the server after adding it. Middleware is applied at startup, so a hot ",
        "reload of the route alone will not pick it up.\n\n",
        "## Avoid\n\n",
        "Do not reach for `mode: 'no-cors'`. It does not enable CORS, it just gives you an ",
        "opaque response you cannot read. And avoid `allow_origins=[\"*\"]` together with ",
        "`allow_credentials=True`: browsers reject that combination.\n\n",
        "## References\n\n",
        "- https://fastapi.tiangolo.com/tutorial/cors/\n",
        "- https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS/Errors\n",
    ],
}

GENERIC = {
    "queries": ["error message current documentation", "recent breaking change"],
    "answer": [
        "## What broke\n\n",
        "This is the mock model, so there is no real analysis here. ",
        "Set `OPENROUTER_API_KEY` and restart the backend to get a real answer.\n\n",
        "```bash\npip install pydantic-settings\n```\n",
    ],
}

# keyed by the height of the uploaded image; the bundled examples are distinct
SCENARIOS = {318: PYDANTIC, 448: NPM_ERESOLVE, 344: CORS}


def _scenario(body: dict) -> dict:
    """Pick a demo scenario from the image the request carries."""
    for msg in body.get("messages", []):
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if part.get("type") != "image_url":
                continue
            url = part.get("image_url", {}).get("url", "")
            if "," not in url:
                continue
            try:
                with Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1]))) as img:
                    return SCENARIOS.get(img.height, GENERIC)
            except Exception:
                return GENERIC
    return GENERIC


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
    scenario = _scenario(body)
    queries = scenario["queries"]

    # Round is derived from the request, not from server state, so a second run
    # behaves exactly like the first.
    done = sum(1 for m in body.get("messages", []) if m.get("role") == "tool")
    capped = body.get("tool_choice") == "none"

    if done < len(queries) and not capped:
        chunks = _tool_round(f"call_{done + 1}", queries[done])
    else:
        chunks = (
            [_chunk({"role": "assistant"})]
            + [_chunk({"content": p}) for p in scenario["answer"]]
            + [_chunk({}, "stop")]
        )

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


def client_at(ip: str) -> httpx.AsyncClient:
    """A client with its own source IP, so the per-IP limiter sees each group
    of checks separately instead of throttling the suite itself."""
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, client=(ip, 5000)),
        base_url="http://test",
    )


async def analyze(client, image: bytes, prompt: str = "") -> list[tuple[str, dict]]:
    res = await client.post("/api/analyze", files={"file": ("shot.png", image, "image/png")},
                            data={"prompt": prompt}, timeout=30)
    assert res.status_code == 200, res.text
    return parse_sse(res.text)


async def run_checks() -> None:
    async with client_at("10.0.0.1") as client:
        # 1) happy path: the generic scenario runs two tool rounds
        events = await analyze(client, png_bytes(), "it broke")
        names = [e for e, _ in events]
        assert names[0] == "compressed" and names[1] == "status", names
        tool_events = [d for e, d in events if e == "tool"]
        assert len(tool_events) == 2, f"expected 2 tool rounds, got {len(tool_events)}"
        assert [t["query"] for t in tool_events] == GENERIC["queries"], tool_events
        answer = "".join(d["text"] for e, d in events if e == "token")
        assert answer == "".join(GENERIC["answer"]), answer
        assert names[-1] == "done", names
        # the model got the tool results back, in order
        assert len(calls) == 3, len(calls)
        tool_msgs = [m for m in calls[2]["messages"] if m["role"] == "tool"]
        assert [m["tool_call_id"] for m in tool_msgs] == ["call_1", "call_2"]
        # image was compressed to fit 1024px
        compressed = events[0][1]
        assert max(compressed["width"], compressed["height"]) <= 1024, compressed
        print("ok: agent loop with 2 tool rounds, streaming, compression")

        # config endpoint exposes the model list the UI reads (no key leaked)
        cfg = (await client.get("/api/config")).json()
        assert cfg["models"] == settings.MODELS and cfg["models"], cfg
        assert "OPENROUTER_API_KEY" not in str(cfg)
        print(f"ok: /api/config reports {len(cfg['models'])} model(s)")

    # 2) each bundled example returns its own answer, and does so repeatably.
    # One source IP per example keeps all of this under the per-IP limit.
    examples = Path(__file__).resolve().parents[2] / "frontend" / "public" / "examples"
    seen: dict[str, str] = {}
    for i, name in enumerate(("python-traceback.png", "npm-eresolve.png", "cors-console.png")):
        path = examples / name
        if not path.is_file():
            print(f"skip: {name} missing, run scripts/make_examples.py")
            continue
        async with client_at(f"10.0.1.{i}") as ex_client:
            first = "".join(d["text"] for e, d in await analyze(ex_client, path.read_bytes()) if e == "token")
            again = "".join(d["text"] for e, d in await analyze(ex_client, path.read_bytes()) if e == "token")
        assert first, f"{name} produced no answer"
        assert first == again, f"{name} not repeatable across runs"
        seen[name] = first

    if len(seen) == 3:
        assert len(set(seen.values())) == 3, "examples returned duplicate answers"
        assert "pydantic-settings" in seen["python-traceback.png"]
        assert "react-day-picker" in seen["npm-eresolve.png"]
        assert "CORSMiddleware" in seen["cors-console.png"]
        print("ok: all 3 examples give distinct, repeatable, on-topic answers")

    # 3) rejections, on their own IP so the 6-request budget is predictable
    async with client_at("10.0.2.1") as c2:
        res = await c2.post("/api/analyze", files={"file": ("x.png", b"not an image", "image/png")})
        assert res.status_code == 415, res.status_code
        res = await c2.post("/api/analyze", files={"file": ("x.png", b"\0" * (5 * 1024 * 1024 + 1), "image/png")})
        assert res.status_code == 413, res.status_code
        bomb = io.BytesIO()
        Image.new("L", (10000, 10000), 0).save(bomb, format="PNG")
        assert bomb.tell() <= 5 * 1024 * 1024
        res = await c2.post("/api/analyze", files={"file": ("bomb.png", bomb.getvalue(), "image/png")})
        assert res.status_code == 413, res.status_code
        print("ok: 415 on non-image, 413 on >5MB and on pixel bomb")

        for expected in (415, 415, 429):
            res = await c2.post("/api/analyze", files={"file": ("x.png", b"junk", "image/png")})
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
