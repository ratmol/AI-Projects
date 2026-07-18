# AI Projects

A collection of Python projects built on LLMs, vision models and real-time web search. Each one is a standalone tool that solves an actual problem rather than a demo.

## Projects

### [Job Search Assistant](./job-search-assistant)

A job search pipeline that pulls structured data out of job posting PDFs, measures your resume against the market, and writes tailored application reports with fit scores, resume tips and interview prep.

* Parses job postings and resumes from PDF using an LLM
* Generates a market wide skills and salary trend report
* Scores your fit for a role from 0 to 100 across required skills, preferred skills and experience
* Produces cover letter guidance and interview questions for a specific posting
* Company research through live web search

Stack: Python, OpenAI SDK, Pydantic v2, pypdf, Tavily, OpenRouter

### [vis-fix](./vis-fix)

A command line debugging assistant. Give it a screenshot of an error and it tells you how to fix it. Works with terminal output, IDE errors, browser consoles and stack traces.

* Takes any screenshot as input, so there is no copy-pasting error text
* Searches the web on its own when it spots version numbers or unfamiliar APIs
* Compresses images before sending them, which keeps latency and API cost down
* Returns an explanation plus a copy-pasteable fix

Stack: Python, OpenAI SDK, Pillow, Tavily, OpenRouter

### [vis-fix-web](./vis-fix-web)

The web version of vis-fix. Paste a screenshot from the clipboard and watch the agent work through it in real time.

* Streams over SSE, so you see compression stats, each web search as it fires, then the answer token by token
* Fixes the CLI's single-tool-call limitation with a proper loop, capped at 5 rounds
* Renders a live timing waterfall of the pipeline, drawn like a browser network panel
* Rate limited, size capped and image validated, since it is meant to be exposed publicly
* Ships as one Docker service, deployable free on Render or Railway

Stack: Python, FastAPI, React, Vite, Tailwind, OpenRouter, Tavily

### [media-utils](./media-utils)

A small library for encoding media files (images, audio, video) to Data URIs and decoding them back to bytes. Useful for embedding media in JSON payloads or LLM API requests without standing up a file server.

* Encode from disk or from raw bytes
* Decode back to bytes or straight to a file
* Handles PNG, JPEG, GIF, WebP, SVG, MP3, WAV, OGG, MP4, WebM
* Validated with Pydantic, so nothing fails silently

Stack: Python, Pydantic v2

## Setup

Each project has its own `requirements.txt` and `.env.example`. Go into the folder you want and follow its README.

```bash
cd job-search-assistant
pip install -r requirements.txt
cp .env.example .env
# add your API keys to .env
```

## API keys

| Service | Used by | Where to get it |
|---|---|---|
| OpenRouter | job-search-assistant, vis-fix, vis-fix-web | [openrouter.ai/keys](https://openrouter.ai/keys) |
| Tavily | job-search-assistant, vis-fix, vis-fix-web | [app.tavily.com](https://app.tavily.com) |
