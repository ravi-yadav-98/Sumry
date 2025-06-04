import asyncio
import traceback
import logging
from typing import List, Dict, Any
import httpx
from langchain.text_splitter import RecursiveCharacterTextSplitter
from api.config import *

logger = logging.getLogger(__name__)

async def summarize_chunk_wrapper(chunk: str, chunk_id: int, total_chunks: int) -> str:
    logger.info("---------------------------------------------------------")
    logger.info(f"🎯 Starting processing of chunk {chunk_id}/{total_chunks}")
    try:
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": "Extract only technical details. No citations or references."},
            {"role": "user", "content": f"Extract technical content: {chunk}"},
        ]
        payload = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            logger.info(f"📤 Sending request for chunk {chunk_id}/{total_chunks}")
            response = await client.post(OLLAMA_API_URL, json=payload)
            response.raise_for_status()
            response_data = response.json()
            summary = response_data["message"]["content"]
            logger.info(f"✅ Completed chunk {chunk_id}/{total_chunks}")
            return summary

    except httpx.TimeoutException as te:
        return f"Error in chunk {chunk_id}: Request timed out. {str(te)}"
    except httpx.ConnectError as ce:
        return f"Error in chunk {chunk_id}: Connection error. {str(ce)}"
    except httpx.HTTPError as he:
        return f"Error in chunk {chunk_id}: HTTP error {str(he)}"
    except Exception as e:
        return f"Error in chunk {chunk_id}: {str(e)}"

async def summarize_chunk_with_retry(chunk: str, chunk_id: int, total_chunks: int, max_retries: int = MAX_RETRIES) -> str:
    retries = 0
    while retries <= max_retries:
        try:
            if retries > 0:
                logger.info(f"🔄 Retry {retries}/{max_retries} for chunk {chunk_id}")
                await asyncio.sleep(RETRY_BACKOFF_BASE * (2 ** (retries - 1)))
            result = await summarize_chunk_wrapper(chunk, chunk_id, total_chunks)
            if not result.startswith("Error"):
                return result
        except Exception as e:
            logger.error(f"Exception: {str(e)}")
        retries += 1
    return f"Error processing chunk {chunk_id} after {max_retries} attempts"

async def summarize_text_parallel(text: str) -> str:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(text)
    logger.info(f"📚 Split into {len(chunks)} chunks")

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
    for retry in range(MAX_RETRIES + 1):
        try:
            payload = {
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
            }
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                response = await client.post(OLLAMA_API_URL, json=payload)
                response.raise_for_status()
                return response.json()["message"]["content"]
        except Exception as e:
            logger.error(f"Final summary retry {retry+1} failed: {e}")
            await asyncio.sleep(5 * (2 ** retry))
    return "Failed to generate final summary."
