import fitz
import logging
logger = logging.getLogger(__name__)


async def extract_text_from_pdf(pdf_path: str) -> str:
    try:
        doc = fitz.open(pdf_path)
        return "\n".join(page.get_text("text") for page in doc)
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        return ""
