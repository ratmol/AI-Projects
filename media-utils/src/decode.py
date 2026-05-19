"""Decode Data URIs back to binary data."""
import base64
import re
from pathlib import Path
from .types import DataURI, VALID_MEDIA_TYPES, get_category

_DATA_URI_RE = re.compile(r"^data:([^;]+);base64,(.+)$")
_BASE64_RE = re.compile(r"^[A-Za-z0-9+/]+=*$")


def _validate_base64(payload: str) -> None:
    if not payload:
        raise ValueError(f"Invalid base64: {payload!r}")
    if not _BASE64_RE.match(payload):
        raise ValueError(f"Invalid base64: {payload[:40]}...")
    # Round-trip check
    round_trip = base64.b64encode(base64.b64decode(payload)).decode()
    if round_trip != payload:
        raise ValueError(f"Invalid base64: {payload[:40]}...")


def parse_data_uri(uri: str) -> DataURI:
    """Parse a Data URI string into its components.

    Raises:
        ValueError: if the string is not a valid Data URI
        ValueError: if the MIME type is unsupported
        ValueError: if the base64 content is invalid
    """
    match = _DATA_URI_RE.match(uri)
    if not match:
        raise ValueError(f"Invalid Data URI: {uri[:80]}")

    mime_type = match.group(1)
    b64 = match.group(2)

    if mime_type not in VALID_MEDIA_TYPES:
        raise ValueError(f"Unsupported MIME type: {mime_type}")

    _validate_base64(b64)

    return DataURI(
        mediaType=mime_type,
        category=get_category(mime_type),
        base64=b64,
        raw=uri,
    )


def decode_to_buffer(uri: str) -> bytes:
    """Decode a Data URI string back into raw binary data."""
    parsed = parse_data_uri(uri)
    raw = base64.b64decode(parsed.base64)
    if parsed.mediaType == "image/svg+xml":
        return raw.decode("utf-8").encode("utf-8")
    return raw


def decode_to_file(uri: str, output_path: str) -> None:
    """Decode a Data URI and write the result to a file."""
    parsed = parse_data_uri(uri)
    path = Path(output_path)
    raw = base64.b64decode(parsed.base64)
    if parsed.mediaType == "image/svg+xml":
        path.write_text(raw.decode("utf-8"), encoding="utf-8")
    else:
        path.write_bytes(raw)
