from fastapi import APIRouter
from ..models import URLRequest
from ..services.summarize_service import summarize_text_parallel
from core.download_pdf import download_pdf
from core.pdf2text import extract_text_from_pdf

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok", "message": "FastAPI backend is running!"}

@router.post("/summarize_arxiv/")
async def summarize_arxiv(request: URLRequest):
    try:
        pdf_path = await download_pdf(request.url)
        if not pdf_path:
            return {"error": "Failed to download PDF. Check the URL."}

        text = await extract_text_from_pdf(pdf_path)
        if not text:
            return {"error": "No text extracted from PDF"}

        summary = await summarize_text_parallel(text)
        return {"summary": summary}
    except Exception as e:
        return {"error": f"Failed to process PDF: {str(e)}"}
