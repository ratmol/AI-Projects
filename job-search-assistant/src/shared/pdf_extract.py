"""PDF text extraction utilities."""
import httpx
from .logger import logger


async def extract_pdf_text(file_path: str) -> str:
    """Extract text from a PDF file or URL."""
    logger.debug(f"Extracting PDF: {file_path}")

    if file_path.startswith("http"):
        url = f"https://r.jina.ai/{file_path}"
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers={"Accept": "text/plain"})
            if res.status_code != 200:
                raise RuntimeError(f"Jina failed: {res.status_code}")
            text = res.text
            logger.debug(f"Jina extracted {len(text)} chars")
            return text

    try:
        import pypdf
        reader = pypdf.PdfReader(file_path)
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages)
        logger.debug(f"Extracted {len(text)} chars")
        return text
    except Exception as err:
        logger.error(f"PDF extraction failed for {file_path}: {err}")
        raise
