from openai import OpenAI
from app.config import settings

_llm_client: OpenAI | None = None
_embed_client: OpenAI | None = None


def get_llm_client() -> OpenAI:
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenAI(
            base_url=settings.OLLAMA_CLOUD_BASE_URL,
            api_key=settings.OLLAMA_CLOUD_API_KEY,
        )
    return _llm_client


def get_embed_client() -> OpenAI:
    global _embed_client
    if _embed_client is None:
        _embed_client = OpenAI(
            base_url=settings.LOCAL_OLLAMA_URL,
            api_key="ollama",
        )
    return _embed_client
