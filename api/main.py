import logging
from fastapi import FastAPI
from .routers import summarize

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Research Summarizer")
app.include_router(summarize.router)

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting FastAPI server at http://localhost:8000")
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
