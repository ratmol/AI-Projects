"""Phase 3: Score fit and generate a tailored application report."""
import asyncio
import json
import re
import sys
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

from ..shared.logger import logger
from ..shared.llm import chat_text
from ..shared.pdf_extract import extract_pdf_text
from ..shared.schemas import JobPosting, Resume
from ..extract.extract_job import extract_job_posting

REPORTS_DIR = Path("reports")
RESUME_DIR = Path("data/resume")


@dataclass
class FitBreakdown:
    required_skills_matched: int
    required_skills_total: int
    preferred_skills_matched: int
    preferred_skills_total: int
    experience_note: str
    education_note: str


@dataclass
class FitScore:
    overall: int
    label: str
    recommendation: str
    breakdown: FitBreakdown


def score_label(score: int) -> tuple[str, str]:
    if score >= 80:
        return (
            "🟢 Strong Fit",
            "You should definitely apply. You meet the core requirements and bring real value to this role.",
        )
    if score >= 50:
        return (
            "🟡 Good Fit",
            "You meet the core requirements. Apply and highlight your strengths — job postings describe ideal candidates, not minimum bars.",
        )
    if score >= 30:
        return (
            "🟠 Stretch Role",
            "Worth applying if this role excites you. Focus on your transferable strengths and show enthusiasm for the gaps you're actively closing.",
        )
    return (
        "🔴 Growth Target",
        "Significant gaps exist, but this is a useful north star. Consider applying speculatively or targeting it in 6–12 months.",
    )


def compute_fit_score(posting: JobPosting, resume: Resume) -> FitScore:
    resume_skills_lower = [
        s.lower()
        for s in (
            resume.hardSkills
            + resume.softSkills
            + resume.keywords
            + [t for p in resume.projects for t in p.technologies]
        )
    ]

    def match_skill(skill: str) -> bool:
        sl = skill.lower()
        return any(sl in rs or rs in sl for rs in resume_skills_lower)

    req_matched = sum(1 for s in posting.requiredSkills if match_skill(s))
    req_total = len(posting.requiredSkills) or 1
    pref_matched = sum(1 for s in posting.preferredSkills if match_skill(s))
    pref_total = len(posting.preferredSkills) or 1

    logger.debug(f"Fit scoring: {req_matched}/{req_total} required skills matched")

    total_months = sum(w.durationMonths or 12 for w in resume.workExperience)
    total_years = total_months / 12
    req_years_str = posting.experienceLevel.years or ""
    m = re.search(r"\d+", req_years_str)
    req_years_num = float(m.group()) if m else 0

    experience_note = (
        f"{total_years:.1f}yr experience vs required {req_years_str} — "
        f"{'meets requirement' if total_years >= req_years_num else 'below requirement'}"
        if req_years_num > 0
        else "Experience requirement not specified"
    )

    req_score = (req_matched / req_total) * 70
    pref_score = (pref_matched / pref_total) * 20
    exp_score = 10 if req_years_num == 0 else (10 if total_years >= req_years_num else (total_years / req_years_num) * 10)
    overall = round(req_score + pref_score + exp_score)

    label, recommendation = score_label(overall)
    return FitScore(
        overall=overall,
        label=label,
        recommendation=recommendation,
        breakdown=FitBreakdown(
            required_skills_matched=req_matched,
            required_skills_total=req_total,
            preferred_skills_matched=pref_matched,
            preferred_skills_total=pref_total,
            experience_note=experience_note,
            education_note=posting.educationRequired or "Not specified",
        ),
    )


async def generate_application_report(
    posting: JobPosting,
    resume: Resume,
    fit: FitScore,
    market_analysis: str,
    gap_report: str,
) -> str:
    fit_section = f"""
## 🎯 Fit Assessment

**Score: {fit.overall}% — {fit.label}**

> {fit.recommendation}

### Score Breakdown
| Category | Result |
|---|---|
| Required Skills | {fit.breakdown.required_skills_matched} / {fit.breakdown.required_skills_total} matched |
| Preferred Skills | {fit.breakdown.preferred_skills_matched} / {fit.breakdown.preferred_skills_total} matched |
| Experience | {fit.breakdown.experience_note} |
| Education | {fit.breakdown.education_note} |
"""

    llm_report = await chat_text(
        """You are a senior career strategist and expert job application coach.
Produce a detailed, specific, and encouraging application report.
Every piece of advice must reference actual content from the job posting, resume, or market data.
Never give generic advice. Be concrete and actionable.
Format as well-structured Markdown.""",
        f"""Produce an application report for this candidate applying to the following role.

## Job Posting:
{json.dumps(posting.model_dump(), indent=2)[:4000]}

## Candidate Resume:
{json.dumps(resume.model_dump(), indent=2)[:4000]}

## Fit Score (already computed — do NOT recompute):
{fit_section}

## Market Context:
{market_analysis[:2000]}

## Candidate Gap Analysis Summary:
{gap_report[:2000]}

---

Generate these three sections ONLY:

## 📝 Resume Adaptation
## ✉️ Cover Letter Guidance
## 🎤 Interview Preparation
""",
    )

    return f"{fit_section}\n\n{llm_report}"


async def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    if len(sys.argv) < 2:
        print(
            "\nUsage: python -m src.advisor.advise <path-to-job-posting.pdf>\n\n"
            "Example:\n  python -m src.advisor.advise data/raw/senior-dev-acme.pdf\n"
        )
        raise SystemExit(1)

    posting_path = Path(sys.argv[1])
    if not posting_path.exists():
        logger.error(f"File not found: {posting_path}")
        raise SystemExit(1)

    resume_json_path = RESUME_DIR / "resume.json"
    if not resume_json_path.exists():
        logger.error("Resume data not found. Run Phase 2 first: python -m src.analysis.gaps")
        raise SystemExit(1)
    resume = Resume.model_validate(json.loads(resume_json_path.read_text()))
    logger.info("Loaded resume data")

    market_path = REPORTS_DIR / "market-analysis.md"
    if not market_path.exists():
        logger.error("Market analysis not found. Run Phase 1 first: python -m src.extract.market")
        raise SystemExit(1)
    market_analysis = market_path.read_text()

    gap_path = REPORTS_DIR / "gap-analysis.md"
    if not gap_path.exists():
        logger.error("Gap analysis not found. Run Phase 2 first: python -m src.analysis.gaps")
        raise SystemExit(1)
    gap_report = gap_path.read_text()

    logger.info(f"Extracting job posting: {posting_path}")
    raw_text = await extract_pdf_text(str(posting_path))
    posting = await extract_job_posting(raw_text)
    logger.info(f"Extracted: {posting.jobTitle} at {posting.companyName}")

    fit = compute_fit_score(posting, resume)
    logger.info(f"Fit score: {fit.overall}% — {fit.label}")

    logger.info("Generating application report...")
    report_body = await generate_application_report(posting, resume, fit, market_analysis, gap_report)

    slug = re.sub(r"\s+", "-", posting_path.stem).lower()
    report_path = REPORTS_DIR / f"application-{slug}.md"
    header = (
        f"# Application Report: {posting.jobTitle or 'Unknown Role'} at {posting.companyName or 'Unknown Company'}\n\n"
        f"_Generated: {datetime.now().isoformat()}_\n_Posting: {posting_path}_\n\n---\n"
    )
    report_path.write_text(header + report_body)
    logger.info(f"Application report saved to {report_path}")

    sal = posting.salaryRange
    sal_str = (
        f"{sal.currency or ''} {sal.min}–{sal.max}"
        if sal.min
        else "Not listed"
    )
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║              APPLICATION REPORT COMPLETE                     ║
╚══════════════════════════════════════════════════════════════╝

Role:     {posting.jobTitle or 'Unknown'} at {posting.companyName or 'Unknown'}
Location: {posting.location or 'Not listed'} ({posting.remoteStatus})
Salary:   {sal_str}

─────────────────────────────────────────────────────────────
FIT SCORE: {fit.overall}%  {fit.label}
─────────────────────────────────────────────────────────────
{fit.recommendation}

Required skills matched: {fit.breakdown.required_skills_matched}/{fit.breakdown.required_skills_total}
Preferred skills matched: {fit.breakdown.preferred_skills_matched}/{fit.breakdown.preferred_skills_total}
Experience: {fit.breakdown.experience_note}

Full report saved to: {report_path}
""")


if __name__ == "__main__":
    asyncio.run(main())
