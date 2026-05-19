"""Image processing: resize and convert to base64."""
import base64
import os
import sys
from pathlib import Path

from PIL import Image
import io


def process_image(image_path: str) -> str:
    """Resize image to fit within 1024x1024 and return as base64 string."""
    absolute_path = Path(image_path).resolve()

    original_size_kb = absolute_path.stat().st_size / 1024
    sys.stderr.write(f"[DEBUG] Original file:    {absolute_path.name}\n")
    sys.stderr.write(f"[DEBUG] Original size:    {original_size_kb:.2f} KB\n")

    # Open and resize with Pillow
    with Image.open(absolute_path) as img:
        # Fit within 1024x1024 without upscaling
        original_w, original_h = img.size
        if original_w > 1024 or original_h > 1024:
            img.thumbnail((1024, 1024), Image.LANCZOS)

        # Convert to JPEG in memory
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=85)
        processed_bytes = buf.getvalue()

    processed_size_kb = len(processed_bytes) / 1024
    sys.stderr.write(f"[DEBUG] Processed size:   {processed_size_kb:.2f} KB\n")

    # If processed is larger than original, use original
    if len(processed_bytes) > absolute_path.stat().st_size:
        sys.stderr.write("[DEBUG] Processed file is larger than original, using original instead\n")
        original_bytes = absolute_path.read_bytes()
        b64 = base64.b64encode(original_bytes).decode()
        sys.stderr.write(f"[DEBUG] Base64 size:      {len(b64)/1024:.2f} KB ({len(b64)} chars)\n")
        return b64

    b64 = base64.b64encode(processed_bytes).decode()
    compression = (1 - len(processed_bytes) / absolute_path.stat().st_size) * 100
    sys.stderr.write(f"[DEBUG] Base64 size:      {len(b64)/1024:.2f} KB ({len(b64)} chars)\n")
    sys.stderr.write(f"[DEBUG] Compression ratio: {compression:.1f}% reduction\n")
    return b64
