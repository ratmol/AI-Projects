"""Phase 2: Extract resume and generate gap analysis report."""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from ..shared.logger import logger
from ..shared.llm import chat_json, chat_text
from ..shared.pdf_extract import extract_pdf_text
from ..shared.schemas import Resume

RESUME_DIR = Path("data/resume")
REPORTS_DIR = Path("reports")
JOBS_DIR = Path("data/jobs")

RESUME_SYSTEM_PROMPT = """You are an expert resume parser and career coach.
Extract structured data from resume text and return ONLY valid JSON.
Focus on how hiring managers and ATS systems evaluate candidates.
For missing fields, use empty arrays or null. Never fabricate values."""

GAP_SYSTEM_PROMPT = """You are a senior career strategist and job market analyst.
Your role is to provide honest, actionable gap analysis between a candidate's resume and market demands.
Be specific and encouraging. Never be generic — every suggestion must reference actual skills or experiences from the data.
Format output as well-structured Markdown with clear sections and triage levels."""


async def extract_resume(raw_text: str) -> Resume:
    """Extract structured resume data from text."""
    logger.debug("Extracting resume fields...")
    logger.debug(f"Resume text sample: {raw_text[:300]}")

    raw = await chat_json(
        RESUME_SYSTEM_PROMPT,
        f"""Extract the following fields from this resume text and return as a single JSON object:
    {{
      "hardSkills": ["Programming languages, frameworks, tools, platforms, databases"],
      "softSkills": ["Communication, leadership, collaboration, problem-solving, etc."],
      "workExperience": [
        {{
          "role": "Job title",
          "company": "Company name",
          "durationMonths": 24,
          "responsibilities": ["Key responsibilities and achievements"]
        }}
      ],
      "education": [
        {{
          "degree": "Degree name",
          "institution": "School name",
          "year": "Graduation year or null"
        }}
      ],
      "certifications": ["Certification names"],
      "projects": [
        {{
          "name": "Project name",
          "description": "Brief description",
          "technologies": ["tech1", "tech2"]
        }}
      ],
      "keywords": ["Industry-specific terms, methodologies, domain expertise"]
    }}
    IMPORTANT: Return a single JSON object, NOT an array.
    Resume text:
    {raw_text[:10000]}""",
    )

    data = raw[0] if isinstance(raw, list) else raw
    logger.debug(f"Resume raw response: {json.dumps(data)[:500]}")

    parsed = Resume.model_validate(data)
    logger.debug(f"Extracted {len(parsed.hardSkills)} hard skills, {len(parsed.workExperience)} roles")
    return parsed


async def generate_gap_report(resume: Resume, market_analysis: str, job_postings: list[dict]) -> str:
    """Generate a detailed gap analysis report."""
    logger.debug("Generating gap analysis report...")

    resume_summary = json.dumps(resume.model_dump(), indent=2)[:6000]
    postings_summary = json.dumps(job_postings, indent=2)[:5000]

    return await chat_text(
        GAP_SYSTEM_PROMPT,
        f"""Analyze this candidate's resume against the job market data and produce a comprehensive gap analysis report.

## Candidate Resume Data:
{resume_summary}

## Market Analysis Report:
{market_analysis[:3000]}

## Raw Job Postings Data (for skills frequency reference):
{postings_summary}

---

Produce a Markdown report with these exact sections:

# Resume Gap Analysis Report

## Executive Summary
2-3 sentence overview of the candidate's market readiness.

## ✅ Strengths (Skills You Have That the Market Wants)
## 🎯 Unique Value (What Makes You Stand Out)
## 🔧 Gaps by Triage Level
### ⚡ Quick Wins (Wording/Framing — fix this week)
### 📅 Short-Term (Days to Weeks)
### 📆 Medium-Term (Weeks to Months)
### 🏗️ Long-Term (Months to Years)
## 📊 Skills Coverage Summary
## 🚀 Recommended Next Steps (Priority Order)
""",
    )


async def main():
    RESUME_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Find resume PDF
    resume_path = None
    cli_arg = sys.argv[1] if len(sys.argv) > 1 else None

    if cli_arg and Path(cli_arg).exists():
        resume_path = cli_arg
        logger.info(f"Using resume from CLI arg: {resume_path}")
    else:
        raw_dir = Path("data/raw")
        if raw_dir.exists():
            resume_files = [f for f in raw_dir.glob("*.pdf") if "resume" in f.name.lower()]
            if resume_files:
                resume_path = str(resume_files[0])
                logger.info(f"Using resume: {resume_path}")
            else:
                all_pdfs = list(raw_dir.glob("*.pdf"))
                if all_pdfs:
                    resume_path = str(all_pdfs[0])
                    logger.info(f"Falling back to: {resume_path}")

    if not resume_path:
        logger.error("No resume PDF found. Place it in data/raw/ or pass path as argument.")
        raise SystemExit(1)

    # Extract or load resume
    resume_json_path = RESUME_DIR / "resume.json"
    if resume_json_path.exists():
        logger.info("Loading existing resume data (delete data/resume/resume.json to re-extract)")
        resume = Resume.model_validate(json.loads(resume_json_path.read_text()))
    else:
        logger.info("Extracting resume from PDF...")
        raw_text = await extract_pdf_text(resume_path)
        resume = await extract_resume(raw_text)
        resume_json_path.write_text(json.dumps(resume.model_dump(), indent=2))
        logger.info(f"Resume data saved to {resume_json_path}")

    # Load market analysis
    market_report_path = REPORTS_DIR / "market-analysis.md"
    if not market_report_path.exists():
        logger.error("Market analysis not found. Run Phase 1 first: python -m src.extract.market")
        raise SystemExit(1)
    market_analysis = market_report_path.read_text()
    logger.info("Loaded market analysis report")

    # Load job postings
    json_files = list(JOBS_DIR.glob("*.json"))
    if not json_files:
        logger.error("No job posting JSON files found. Run Phase 1 first.")
        raise SystemExit(1)
    all_postings = [json.loads(f.read_text()) for f in json_files]
    logger.info(f"Loaded {len(all_postings)} job postings for comparison")

    # Generate gap report
    logger.info("Generating gap analysis report...")
    gap_report = await generate_gap_report(resume, market_analysis, all_postings)

    report_path = REPORTS_DIR / "gap-analysis.md"
    report_path.write_text(
        f"# Resume Gap Analysis\n\n_Generated: {datetime.now().isoformat()}_\n\n{gap_report}"
    )
    logger.info(f"Gap analysis saved to {report_path}")
    print(f"\nDone. Report saved to {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
