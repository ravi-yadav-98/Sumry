import fitz
import httpx
import logging

logger = logging.getLogger(__name__)

async def download_pdf(url: str) -> str | None:
    if not url.startswith("https://arxiv.org/pdf/"):
        logger.error(f"Invalid URL: {url}")
        return None

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()

            if "application/pdf" not in response.headers.get("Content-Type", ""):
                logger.error(f"Invalid content type: {response.headers.get('Content-Type')}")
                return None

            filename = "arxiv_paper.pdf"
            with open(filename, "wb") as f:
                f.write(response.content)
            return filename
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return None

async def extract_text_from_pdf(pdf_path: str) -> str:
    try:
        doc = fitz.open(pdf_path)
        return "\n".join(page.get_text("text") for page in doc)
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        return ""
