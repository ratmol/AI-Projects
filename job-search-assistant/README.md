# Job Search Assistant 🔍

An AI-powered job search pipeline that analyzes job postings, compares them against your resume, and generates tailored application reports — all from PDFs, fully automated.

Built with Python, OpenAI SDK, and Pydantic. Uses OpenRouter to access Gemini/GPT-4/Claude interchangeably.

---

## What It Does

This tool runs in three phases:

**Phase 1 — Market Analysis**
Drop job posting PDFs into `data/raw/`. The tool extracts structured data from each one (skills, salary, experience requirements, company info) using an LLM, then generates a market-wide report summarizing trends, most-wanted skills, and salary ranges.

**Phase 2 — Gap Analysis**
Point it at your resume PDF. It parses your skills, experience, and projects, then compares them against the market data and produces a prioritized gap report — triaged into quick wins, short-term goals, and long-term targets.

**Phase 3 — Application Advisor**
Pass any job posting PDF and get a full application report: a 0–100% fit score, resume tailoring suggestions for that specific role, cover letter guidance, and interview prep questions drawn from the actual posting.

---

## Tech Stack

- **Python 3.11+**
- **OpenAI SDK** — pointed at [OpenRouter](https://openrouter.ai) for model flexibility
- **Pydantic v2** — structured data validation for LLM outputs
- **pypdf** — local PDF text extraction
- **httpx** — async HTTP client
- **Tavily** — real-time web search for company research

---

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in your keys
```

```env
OPENROUTER_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
LOG_LEVEL=info
```

---

## Usage

```bash
# Phase 1 — extract job postings and generate market report
python -m src.extract.market

# Phase 2 — parse resume and generate gap analysis
python -m src.analysis.gaps

# Phase 3 — score fit and generate application report for a specific role
python -m src.advisor.advise data/raw/job-posting.pdf
```

---

## Project Structure

```
job-search-assistant/
├── src/
│   ├── shared/
│   │   ├── llm.py            # OpenRouter client, chat_json / chat_text helpers
│   │   ├── schemas.py        # Pydantic models — JobPosting, Resume, etc.
│   │   ├── pdf_extract.py    # PDF text extraction (local + URL via Jina)
│   │   ├── search.py         # Tavily web search wrapper
│   │   └── logger.py         # Lightweight stderr logger
│   ├── extract/
│   │   ├── extract_job.py    # LLM-based job posting parser
│   │   └── market.py         # Phase 1 entry point
│   ├── analysis/
│   │   └── gaps.py           # Phase 2 entry point
│   └── advisor/
│       └── advise.py         # Phase 3 entry point + fit scoring logic
├── data/
│   ├── raw/                  # Drop PDFs here
│   ├── jobs/                 # Extracted job JSON (auto-generated)
│   └── resume/               # Extracted resume JSON (auto-generated)
├── reports/                  # Generated Markdown reports
├── requirements.txt
└── .env.example
```

---

## Fit Scoring

The advisor scores your fit for a role using three weighted factors:

| Factor | Weight |
|---|---|
| Required skills matched | 70% |
| Preferred skills matched | 20% |
| Years of experience | 10% |

| Score | Label |
|---|---|
| ≥ 80% | 🟢 Strong Fit |
| ≥ 50% | 🟡 Good Fit |
| ≥ 30% | 🟠 Stretch Role |
| < 30% | 🔴 Growth Target |