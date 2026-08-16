import json
import logging
import re
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMUnavailableError(RuntimeError):
    """Raised when no LLM provider is configured."""


class AIProvider:
    """OpenAI-compatible LLM client (works with OpenAI, Gemini, Ollama, etc.)."""

    def __init__(self) -> None:
        self._client: Any = None

    @property
    def client(self) -> Any:
        if self._client is None:
            if not settings.OPENAI_API_KEY:
                raise LLMUnavailableError("No OPENAI_API_KEY configured")
            try:
                from openai import OpenAI

                self._client = OpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    base_url=settings.OPENAI_BASE_URL or None,
                )
            except ImportError:
                raise LLMUnavailableError("openai package not installed")
        return self._client

    @property
    def available(self) -> bool:
        return bool(settings.OPENAI_API_KEY)

    def complete(self, system: str, user: str, temperature: float = 0.2, max_tokens: int = 1500) -> str:
        resp = self.client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content or ""

    def complete_json(self, system: str, user: str, temperature: float = 0.0) -> dict:
        """Request JSON output and parse it robustly."""
        text = self.complete(system=system, user=user, temperature=temperature)
        return parse_json(text)

    def embed(self, text: str) -> list[float]:
        resp = self.client.embeddings.create(model=settings.EMBEDDING_MODEL, input=[text])
        return resp.data[0].embedding


def parse_json(text: str) -> dict:
    """Best-effort parse of a JSON object that may be wrapped in markdown fences."""
    if not text:
        raise ValueError("empty LLM response")
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


def get_provider() -> AIProvider:
    return AIProvider()
