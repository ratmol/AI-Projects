"""Media type definitions and helpers."""
from __future__ import annotations
from typing import Literal, get_args
from pydantic import BaseModel, field_validator

MediaType = Literal[
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
    "image/svg+xml",
    "audio/mpeg",
    "audio/wav",
    "audio/ogg",
    "video/mp4",
    "video/webm",
]

VALID_MEDIA_TYPES: set[str] = set(get_args(MediaType))

MediaCategory = Literal["image", "audio", "video"]

EXTENSION_TO_MIME: dict[str, str] = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
    "svg": "image/svg+xml",
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "ogg": "audio/ogg",
    "mp4": "video/mp4",
    "webm": "video/webm",
}


def get_category(mime_type: str) -> MediaCategory:
    return mime_type.split("/")[0]  # type: ignore[return-value]


class DataURI(BaseModel):
    mediaType: str
    category: str
    base64: str
    raw: str

    @field_validator("mediaType")
    @classmethod
    def validate_mime(cls, v: str) -> str:
        if v not in VALID_MEDIA_TYPES:
            raise ValueError(f"Unsupported MIME type: {v}")
        return v

    @field_validator("base64")
    @classmethod
    def validate_base64_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("base64 must not be empty")
        return v

    @field_validator("raw")
    @classmethod
    def validate_raw_prefix(cls, v: str) -> str:
        if not v.startswith("data:"):
            raise ValueError("raw must start with 'data:'")
        return v
