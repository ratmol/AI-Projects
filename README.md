# AI Projects 

A collection of AI-powered Python projects built with LLMs, computer vision, and real-time web search. Each project is a standalone tool that solves a real problem using modern AI APIs.

---

## Projects

### 🔍 [Job Search Assistant](./job-search-assistant)
An end-to-end job search pipeline that extracts structured data from job posting PDFs, analyzes your resume against the market, and generates tailored application reports with fit scores, resume tips, and interview prep.

**Key features:**
- Parses job postings and resumes from PDF using an LLM
- Generates a market-wide skills and salary trend report
- Scores your fit for any role (0–100%) across required skills, preferred skills, and experience
- Produces tailored cover letter guidance and interview questions per posting
- Real-time company research via web search

**Stack:** Python · OpenAI SDK · Pydantic v2 · pypdf · Tavily · OpenRouter

---

### 🔧 [vis-fix](./vis-fix)
A command-line debugging assistant that takes a screenshot of an error and tells you how to fix it. Works with terminal output, IDE errors, browser consoles, and stack traces.

**Key features:**
- Accepts any screenshot as input — no copy-pasting error text
- Automatically searches the web when it detects version numbers or unfamiliar APIs
- Compresses images before sending to keep latency and API costs low
- Outputs a structured explanation and a copy-pasteable fix

**Stack:** Python · OpenAI SDK · Pillow · Tavily · OpenRouter

---

### 📦 [media-utils](./media-utils)
A lightweight utility library for encoding media files (images, audio, video) to Data URIs and decoding them back to raw bytes. Useful for embedding media in JSON payloads or LLM API requests without a file server.

**Key features:**
- Encode files from disk or raw bytes to Data URIs
- Decode Data URIs back to bytes or write directly to a file
- Supports PNG, JPEG, GIF, WebP, SVG, MP3, WAV, OGG, MP4, WebM
- Fully validated with Pydantic — no silent failures

**Stack:** Python · Pydantic v2

---

## Setup

Each project has its own `requirements.txt` and `.env.example`. Navigate into any project folder and follow its README to get started.

```bash
cd job-search-assistant
pip install -r requirements.txt
cp .env.example .env
# Add your API keys to .env
```

---

## API Keys Needed

| Service | Used By | Get It |
|---|---|---|
| OpenRouter | job-search-assistant, vis-fix | [openrouter.ai/keys](https://openrouter.ai/keys) |
| Tavily | job-search-assistant, vis-fix | [app.tavily.com](https://app.tavily.com) |
