# app/llm/ollama_client.py

import logging
import httpx
from typing import List, Dict, Optional
from config.settings import OLLAMA_API_URL, OLLAMA_MODEL, HTTP_TIMEOUT

logger = logging.getLogger(__name__)

async def call_ollama(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    stream: bool = False
) -> str:
    model = model or OLLAMA_MODEL

    payload = {
        "model": model,
        "messages": messages,
        "stream": stream,
    }

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.post(OLLAMA_API_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ HTTP error while calling LLM: {e}")
        raise
    except httpx.RequestError as e:
        logger.error(f"❌ Request error while calling LLM: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in LLM call: {e}")
        raise
