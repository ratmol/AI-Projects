"""Encode media files to Data URIs."""
import base64
from pathlib import Path
from .types import DataURI, EXTENSION_TO_MIME, VALID_MEDIA_TYPES, get_category


def encode_file(file_path: str) -> DataURI:
    """Read a media file from disk and return it as a Data URI.

    Raises:
        FileNotFoundError: if the file doesn't exist
        ValueError: if the extension is unsupported or the file is empty
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = path.suffix.lstrip(".").lower()
    mime_type = EXTENSION_TO_MIME.get(ext)
    if not mime_type:
        raise ValueError(f"Unsupported extension: {path.suffix or ext}")

    data = path.read_bytes()
    if len(data) == 0:
        raise ValueError(f"Empty file: {file_path}")

    b64 = base64.b64encode(data).decode()
    return DataURI(
        mediaType=mime_type,
        category=get_category(mime_type),
        base64=b64,
        raw=f"data:{mime_type};base64,{b64}",
    )


def encode_buffer(data: bytes, mime_type: str) -> DataURI:
    """Encode raw bytes as a Data URI with the given MIME type.

    Raises:
        ValueError: if the MIME type is unsupported or data is empty
    """
    if mime_type not in VALID_MEDIA_TYPES:
        raise ValueError(f"Unsupported MIME type: {mime_type}")

    if len(data) == 0:
        raise ValueError(f"Empty data")

    b64 = base64.b64encode(data).decode()
    return DataURI(
        mediaType=mime_type,
        category=get_category(mime_type),
        base64=b64,
        raw=f"data:{mime_type};base64,{b64}",
    )
