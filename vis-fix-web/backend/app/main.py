"""FastAPI app: streaming /api/analyze endpoint + static frontend hosting."""
import base64
import io
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from . import settings
from .agent import run_analysis
from .image_processor import compress_image

logging.basicConfig(level=logging.INFO)

# Screenshots are never this large; a 5MB file can still decode to a
# multi-GB pixel bomb without this cap.
Image.MAX_IMAGE_PIXELS = 40_000_000

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.validate()
    yield


app = FastAPI(title="vis-fix", lifespan=lifespan, docs_url=None, redoc_url=None)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def _sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/config")
async def config():
    """Public, non-secret runtime config so the UI reflects the real model
    instead of a hardcoded name."""
    return {"models": settings.MODELS}


@app.post("/api/analyze")
@limiter.limit(settings.RATE_LIMIT)
async def analyze(request: Request, file: UploadFile, prompt: str = Form("")):
    raw = await file.read(settings.MAX_UPLOAD_BYTES + 1)
    if len(raw) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Image is larger than 5 MB.")
    if not raw:
        raise HTTPException(400, "Empty upload.")

    # Trust the bytes, not the Content-Type header: Pillow must parse it.
    try:
        with Image.open(io.BytesIO(raw)) as img:
            img.verify()
    except Image.DecompressionBombError:
        raise HTTPException(413, "Image dimensions are too large.")
    except (UnidentifiedImageError, OSError):
        raise HTTPException(415, "File is not a readable image.")

    user_prompt = prompt.strip()[: settings.MAX_PROMPT_CHARS] or (
        "Please analyze this screenshot and help me fix the error."
    )

    compressed, mime, stats = await run_in_threadpool(compress_image, raw)
    image_b64 = base64.b64encode(compressed).decode()

    async def event_stream():
        yield _sse("compressed", {**stats, "data_url": f"data:{mime};base64,{image_b64}"})
        async for event, payload in run_analysis(image_b64, mime, user_prompt):
            yield _sse(event, payload)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# Registered last so /api/* routes win; serves the built frontend in production.
DIST_DIR = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if DIST_DIR.is_dir():
    app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="frontend")
