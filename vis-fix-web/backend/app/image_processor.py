"""Server-side image compression: fit within 1024x1024, re-encode as JPEG."""
import io

from PIL import Image

MAX_DIMENSION = 1024
JPEG_QUALITY = 85


def compress_image(data: bytes) -> tuple[bytes, str, dict]:
    """Return (image_bytes, mime, stats) ready to send to the model.

    Token cost scales with pixel count, so a resize always wins. The
    keep-the-original fallback only applies when no resize happened and
    JPEG re-encoding grew the payload (e.g. small crisp PNGs).
    """
    with Image.open(io.BytesIO(data)) as img:
        original_format = (img.format or "png").lower()
        resized = img.width > MAX_DIMENSION or img.height > MAX_DIMENSION
        if resized:
            img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)
        width, height = img.size

        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=JPEG_QUALITY)
        processed = buf.getvalue()

    if not resized and len(processed) >= len(data):
        processed, mime = data, f"image/{original_format}"
    else:
        mime = "image/jpeg"

    stats = {
        "original_kb": round(len(data) / 1024, 1),
        "final_kb": round(len(processed) / 1024, 1),
        "width": width,
        "height": height,
    }
    return processed, mime, stats
