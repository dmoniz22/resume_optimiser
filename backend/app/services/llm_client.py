import json
import httpx
from openai import OpenAI
from app.config import settings

_llm_client: httpx.Client | None = None
_embed_client: OpenAI | None = None


class LLMResponse:
    def __init__(self, content: str):
        self.choices = [LLMChoice(content)]


class LLMChoice:
    def __init__(self, content: str):
        self.message = LLMMessage(content)


class LLMMessage:
    def __init__(self, content: str):
        self.content = content


class LLMClient:
    def __init__(self):
        self._client = httpx.Client(verify=False, timeout=300)

    @property
    def chat(self):
        return self

    @property
    def completions(self):
        return self

    def create(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 4096,
        response_format: dict | None = None,
        **kwargs,
    ) -> LLMResponse:
        body: dict = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        resp = self._client.post(
            f"{settings.OLLAMA_CLOUD_BASE_URL}/api/chat",
            json=body,
            headers={
                "Authorization": f"Bearer {settings.OLLAMA_CLOUD_API_KEY}",
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return LLMResponse(data["message"]["content"])


def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


def get_embed_client() -> OpenAI:
    global _embed_client
    if _embed_client is None:
        _embed_client = OpenAI(
            base_url=settings.LOCAL_OLLAMA_URL,
            api_key="ollama",
        )
    return _embed_client
