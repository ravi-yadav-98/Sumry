import httpx

OLLAMA_API_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "gemma3:latest"
CHUNK_SIZE = 10000
CHUNK_OVERLAP = 100
MAX_RETRIES = 2
RETRY_BACKOFF_BASE = 5  # in seconds

HTTP_TIMEOUT = httpx.Timeout(connect=60, read=3600, write=60, pool=60)
