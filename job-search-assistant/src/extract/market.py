"""Phase 1: Extract job postings from PDFs and generate market analysis."""
import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from ..shared.logger import logger
from ..shared.llm import chat_text
from ..shared.pdf_extract import extract_pdf_text
from .extract_job import extract_job_posting

PDF_DIR = Path("data/raw")
JOBS_DIR = Path("data/jobs")
REPORTS_DIR = Path("reports")


async def main():
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    files = list(PDF_DIR.glob("*.pdf"))
    if not files:
        logger.error(f"No PDFs found in {PDF_DIR}. Drop your job posting PDFs there and re-run.")
        raise SystemExit(1)

    logger.info(f"Found {len(files)} PDF(s) in {PDF_DIR}")

    for pdf_file in files:
        slug = pdf_file.stem.replace(" ", "-").lower()
        output_path = JOBS_DIR / f"{slug}.json"

        if output_path.exists():
            logger.info(f"Skipping {pdf_file.name} (already extracted)")
            continue

        logger.info(f"Processing: {pdf_file.name}")
        try:
            raw_text = await extract_pdf_text(str(pdf_file))
            posting = await extract_job_posting(raw_text)
            output_path.write_text(json.dumps(posting.model_dump(), indent=2))
            logger.info(f"Saved: {output_path}")
        except Exception as err:
            logger.error(f"Failed to process {pdf_file.name}: {err}")

    # Generate market analysis report
    logger.info("Generating market analysis report...")
    json_files = list(JOBS_DIR.glob("*.json"))
    all_postings = [json.loads(f.read_text()) for f in json_files]

    report = await chat_text(
        "You are a job market analyst writing a report for a job seeker. Be specific and data-driven.\n"
        "Format the output as well-structured Markdown.",
        f"""Analyze these {len(all_postings)} job postings and produce a comprehensive market analysis report.

     Include sections for:
     1. Most commonly required skills and technologies (with frequency counts)
     2. Preferred/nice-to-have skills
     3. Typical experience levels and seniority expectations
     4. Education requirements
     5. Salary ranges (if available)
     6. Common responsibilities and role patterns
     7. Notable trends and observations
     8. Company profiles summary

     Posting data:
     {json.dumps(all_postings, indent=2)[:12000]}""",
    )

    from datetime import datetime
    report_path = REPORTS_DIR / "market-analysis.md"
    report_path.write_text(f"# Job Market Analysis\n\n_Generated: {datetime.now().isoformat()}_\n\n{report}")
    logger.info(f"Market analysis saved to {report_path}")
    print(f"\nDone. Report saved to {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
