# AGENTS.md

## Project

A utility library for encoding and decoding media files as Base64 Data URIs.
Supports images (PNG, JPEG, GIF, WebP, SVG), audio (MP3, WAV, OGG), and
video (MP4, WebM) formats.

## Tech Stack

- TypeScript (strict mode) with Node.js built-in APIs
- Zod for runtime schema validation
- Vitest for unit testing

## Structure

```
src/
  types.ts       — Zod schemas, MIME map, MediaType/DataURI types
  encode.ts      — encodeFile(filePath), encodeBuffer(data, mimeType)
  decode.ts      — parseDataURI(uri), decodeToBuffer(uri), decodeToFile(uri, path)
  index.ts       — Re-exports all public API

tests/
  encode.test.ts — Tests for encoding functions
  decode.test.ts — Tests for decoding functions
  fixtures/      — Minimal real media files (png, jpg, gif, webp, svg, mp3, mp4)
```

## Commands

```bash
npm test          # Run all tests once (vitest run)
npm run test:watch  # Watch mode
npm run typecheck   # TypeScript type-check only (tsc --noEmit)
```

## Conventions

- All public functions must have JSDoc comments matching the existing stubs
- Validate inputs/outputs with Zod schemas — never return unvalidated data
- Handle errors explicitly with descriptive messages (include the bad value)
- SVG is text-based — encode/decode it differently from binary formats
- Prefer Node.js built-in `fs` and `Buffer` APIs — no third-party binary libs
- Keep functions small and single-purpose
- Run `npm test` after every change to verify progress

## Key Types

- `DataURI` — `{ mediaType, category, base64, raw }` (Zod-validated)
- `MediaType` — union of all 10 supported MIME strings
- `EXTENSION_TO_MIME` — maps file extensions → MIME types (no leading dot)

## Error Contract

| Situation                        | Expected behaviour                |
| -------------------------------- | --------------------------------- |
| File not found                   | Throw with path in message        |
| Unsupported extension/MIME type  | Throw with the bad value included |
| Empty file or empty data buffer  | Throw "empty" error               |
| Malformed Data URI string        | Throw with reason                 |
| Invalid Base64 payload           | Throw with reason                 |