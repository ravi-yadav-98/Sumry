import asyncio
import logging
from typing import List, Dict

from langchain.text_splitter import RecursiveCharacterTextSplitter

from .ollama_client import call_ollama
from config.settings import (
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    MAX_RETRIES,
    RETRY_BACKOFF_BASE
)

logger = logging.getLogger(__name__)

# ---------------------- Chunk Summarization ---------------------- #

async def summarize_chunk(chunk: str, chunk_id: int, total_chunks: int) -> str:
    logger.info(f"🎯 Summarizing chunk {chunk_id}/{total_chunks}")
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": "Extract only technical details. No citations or references."},
        {"role": "user", "content": f"Extract technical content: {chunk}"},
    ]
    try:
        return await call_ollama(messages)
    except Exception as e:
        return f"Error in chunk {chunk_id}: {str(e)}"

async def summarize_chunk_with_retry(chunk: str, chunk_id: int, total_chunks: int) -> str:
    for attempt in range(MAX_RETRIES + 1):
        if attempt > 0:
            logger.info(f"🔄 Retry {attempt}/{MAX_RETRIES} for chunk {chunk_id}")
            await asyncio.sleep(RETRY_BACKOFF_BASE * (2 ** (attempt - 1)))
        result = await summarize_chunk(chunk, chunk_id, total_chunks)
        if not result.startswith("Error"):
            return result
    return f"Error processing chunk {chunk_id} after {MAX_RETRIES} attempts"

# ---------------------- Text Splitting & Parallel Summarization ---------------------- #

async def summarize_text_parallel(text: str) -> str:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(text)
    logger.info(f"📚 Text split into {len(chunks)} chunks")

    tasks = [
        summarize_chunk_with_retry(chunk, i + 1, len(chunks))
        for i, chunk in enumerate(chunks)
    ]
    summaries = await asyncio.gather(*tasks)

    successful = [s for s in summaries if not s.startswith("Error")]
    if not successful:
        return "All chunks failed to summarize."

    combined = "\n\n".join(f"Section {i+1}:\n{summary}" for i, summary in enumerate(summaries))
    return await generate_final_summary(combined)

# ---------------------- Final Summary Generation ---------------------- #

async def generate_final_summary(combined_chunk_summaries: str) -> str:
    messages = [
        {"role": "system", "content": "You are a technical writer. No citations. Technical focus only."},
        {"role": "user", "content": f"""Create a technical document structured into:
1. System Architecture
2. Technical Implementation
3. Infrastructure & Setup
4. Performance Analysis
5. Optimization Techniques

Only use the following content:
{combined_chunk_summaries}
"""}
    ]
    for attempt in range(MAX_RETRIES + 1):
        try:
            return await call_ollama(messages)
        except Exception as e:
            logger.error(f"❌ Final summary retry {attempt + 1} failed: {e}")
            await asyncio.sleep(5 * (2 ** attempt))
    return "Failed to generate final summary."
