# media-utils

A small Python library for encoding media files to Data URIs and decoding them back to raw bytes. Pydantic is the only dependency.

Handy for embedding images, audio or video directly in JSON payloads, LLM API requests, or HTML, without standing up a file server or CDN.

## Supported formats

| Category | Formats |
|---|---|
| Image | PNG, JPEG, GIF, WebP, SVG |
| Audio | MP3, WAV, OGG |
| Video | MP4, WebM |

## Usage

Encode a file from disk:

```python
from src import encode_file

uri = encode_file("photo.png")

print(uri.raw)        # data:image/png;base64,iVBOR...
print(uri.mediaType)  # image/png
print(uri.category)   # image
print(uri.base64)     # raw base64 string
```

Encode raw bytes:

```python
from src import encode_buffer

with open("clip.mp3", "rb") as f:
    data = f.read()

uri = encode_buffer(data, "audio/mpeg")
print(uri.raw)  # data:audio/mpeg;base64,...
```

Parse a Data URI string:

```python
from src import parse_data_uri

uri = parse_data_uri("data:image/jpeg;base64,/9j/4AAQ...")
print(uri.category)   # image
print(uri.mediaType)  # image/jpeg
```

Decode back to bytes or straight to a file:

```python
from src import decode_to_buffer, decode_to_file

raw_bytes = decode_to_buffer("data:image/png;base64,...")

decode_to_file("data:image/png;base64,...", "output.png")
```

## API

| Function | Description |
|---|---|
| `encode_file(path)` | Read a file from disk, returns `DataURI` |
| `encode_buffer(data, mime_type)` | Encode raw bytes, returns `DataURI` |
| `parse_data_uri(uri)` | Parse a Data URI string, returns `DataURI` |
| `decode_to_buffer(uri)` | Data URI string to `bytes` |
| `decode_to_file(uri, path)` | Data URI string to a file on disk |

Bad input raises `ValueError` or `FileNotFoundError` with a description of what went wrong. Nothing fails silently.

## The DataURI model

```python
class DataURI(BaseModel):
    mediaType: str   # e.g. "image/png"
    category: str    # "image", "audio", or "video"
    base64: str      # base64-encoded content
    raw: str         # full data URI string
```

## Setup

```bash
pip install -r requirements.txt
```

Or just copy the `src/` folder into your project. Pydantic is the only thing it needs.

## Project structure

```
media-utils/
├── src/
│   ├── __init__.py   # public exports
│   ├── types.py      # DataURI model, MIME type map, helpers
│   ├── encode.py     # encode_file, encode_buffer
│   └── decode.py     # parse_data_uri, decode_to_buffer, decode_to_file
└── requirements.txt
```
