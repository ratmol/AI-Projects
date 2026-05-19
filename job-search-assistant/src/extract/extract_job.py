"""Extract structured data from job posting text."""
import json
from ..shared.llm import chat_json
from ..shared.search import web_search
from ..shared.schemas import JobPosting, CompanyResearch
from ..shared.logger import logger

SYSTEM_PROMPT = """You are an expert job market analyst.
Extract structured data from job postings and return ONLY valid JSON.
The text may contain formatting artifacts from PDF extraction — ignore them and focus on the content.
For any field not found in the posting, use null. Never fabricate values."""


async def extract_job_posting(raw_text: str) -> JobPosting:
    """Extract a structured JobPosting from raw text."""
    logger.debug("Extracting job posting fields...")
    logger.debug(f"Raw text sample: {raw_text[:300]}")

    raw = await chat_json(
        SYSTEM_PROMPT,
        f"""Extract the following fields from this job posting text and return as JSON:
    {{
      "jobTitle": "exact job title string",
      "companyName": "company name string",
      "location": "city, country or remote",
      "remoteStatus": "remote" | "hybrid" | "on-site" | "not listed",
      "requiredSkills": ["skill1", "skill2"],
      "preferredSkills": ["skill1", "skill2"],
      "experienceLevel": {{ "years": "3-5 years", "seniority": "mid-level" }},
      "educationRequired": "Bachelor's degree or null",
      "salaryRange": {{ "min": 80000, "max": 120000, "currency": "CAD" }},
      "responsibilities": ["responsibility1", "responsibility2"],
      "companyResearch": {{ "size": null, "industry": null, "recentNews": null, "cultureNotes": null }}
    }}
    IMPORTANT: Return a single JSON object, NOT an array.
    Job posting text:
    {raw_text[:8000]}""",
    )

    data: dict = raw[0] if isinstance(raw, list) else raw
    logger.debug(f"LLM raw response: {json.dumps(data)[:500]}")

    # Research company
    company_name = str(data.get("companyName") or "")
    if company_name and company_name not in ("not listed", "null"):
        logger.debug(f"Researching company: {company_name}")
        try:
            results = await web_search(f"{company_name} company size industry")
            news_results = await web_search(f"{company_name} news 2025")
            research_ctx = "\n".join(f"{r.title}: {r.content}" for r in results)[:2000]
            news_ctx = "\n".join(f"{r.title}: {r.content}" for r in news_results)[:1000]
            research = await chat_json(
                "Extract company research into JSON with fields: size, industry, recentNews, cultureNotes. Use null if not found.",
                f"Company: {company_name}\nSearch results:\n{research_ctx}\nNews:\n{news_ctx}",
            )
            data["companyResearch"] = research
        except Exception as err:
            logger.error(f"Company research failed for {company_name}: {err}")
            data["companyResearch"] = {"size": None, "industry": None, "recentNews": None, "cultureNotes": None}

    posting = JobPosting.model_validate(data)
    logger.debug(f"Extracted: {posting.jobTitle} at {posting.companyName}")
    logger.debug(f"Required skills: {len(posting.requiredSkills)}, Preferred: {len(posting.preferredSkills)}")
    return posting
