# Job Search Assistant

An AI job search pipeline that reads job postings, compares them against your resume, and writes tailored application reports. Everything runs off PDFs.

Built with Python, the OpenAI SDK and Pydantic, using OpenRouter so Gemini, GPT-4 and Claude are interchangeable.

## What it does

Three phases, run independently.

**Phase 1, market analysis.** Drop job posting PDFs into `data/raw/`. Each one gets parsed into structured data (skills, salary, experience requirements, company info) by an LLM, then rolled up into a market wide report covering trends, the most requested skills, and salary ranges.

**Phase 2, gap analysis.** Point it at your resume PDF. It pulls out your skills, experience and projects, compares them against the market data, and produces a prioritized gap report split into quick wins, short term goals and long term targets.

**Phase 3, application advisor.** Give it a single job posting PDF and it returns a full application report: a fit score out of 100, resume tailoring suggestions for that specific role, cover letter guidance, and interview questions drawn from the actual posting.

## Tech stack

Python 3.11+, with:

* OpenAI SDK, pointed at [OpenRouter](https://openrouter.ai) for model flexibility
* Pydantic v2 for validating LLM output into structured data
* pypdf for local PDF text extraction
* httpx as the async HTTP client
* Tavily for company research via web search

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# fill in your keys
```

```env
OPENROUTER_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
LOG_LEVEL=info
```

## Usage

```bash
# phase 1: extract job postings and generate the market report
python -m src.extract.market

# phase 2: parse the resume and generate the gap analysis
python -m src.analysis.gaps

# phase 3: score fit and write the application report for one role
python -m src.advisor.advise data/raw/job-posting.pdf
```

## Project structure

```
job-search-assistant/
├── src/
│   ├── shared/
│   │   ├── llm.py            # OpenRouter client, chat_json / chat_text helpers
│   │   ├── schemas.py        # Pydantic models: JobPosting, Resume, etc.
│   │   ├── pdf_extract.py    # PDF text extraction (local + URL via Jina)
│   │   ├── search.py         # Tavily web search wrapper
│   │   └── logger.py         # lightweight stderr logger
│   ├── extract/
│   │   ├── extract_job.py    # LLM-based job posting parser
│   │   └── market.py         # phase 1 entry point
│   ├── analysis/
│   │   └── gaps.py           # phase 2 entry point
│   └── advisor/
│       └── advise.py         # phase 3 entry point + fit scoring
├── data/
│   ├── raw/                  # drop PDFs here
│   ├── jobs/                 # extracted job JSON (generated)
│   └── resume/               # extracted resume JSON (generated)
├── reports/                  # generated Markdown reports
├── requirements.txt
└── .env.example
```

## Fit scoring

Three weighted factors:

| Factor | Weight |
|---|---|
| Required skills matched | 70% |
| Preferred skills matched | 20% |
| Years of experience | 10% |

Which maps to:

| Score | Label |
|---|---|
| 80% and up | Strong fit |
| 50% to 79% | Good fit |
| 30% to 49% | Stretch role |
| Under 30% | Growth target |
