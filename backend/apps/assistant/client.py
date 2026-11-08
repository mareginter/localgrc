"""Thin wrapper around the Ollama SDK, configured from Django settings.

Keeps all Ollama-specific logic in one place so the rest of the app
only ever talks to `AssistantClient`.
"""

import logging

import ollama
from django.conf import settings

logger = logging.getLogger(__name__)


class AssistantClient:
    def __init__(self):
        self.host = getattr(settings, "OLLAMA_HOST", "http://ollama:11434")
        self.model = getattr(settings, "OLLAMA_MODEL", "llama3.1:8b")
        self.embed_model = getattr(settings, "OLLAMA_EMBED_MODEL", "nomic-embed-text")
        self.timeout = getattr(settings, "OLLAMA_TIMEOUT", 120)
        self._client = ollama.Client(host=self.host, timeout=self.timeout)

    # ---- Health / models ----
    def is_available(self) -> bool:
        try:
            self._client.list()
            return True
        except Exception:
            logger.exception("Ollama unavailable")
            return False

    def list_models(self) -> list[str]:
        """Return model names. Handles both dict and Pydantic response shapes
        across ollama SDK versions (0.4+ returns dict, 0.5+ returns ListResponse)."""
        try:
            response = self._client.list()
            if isinstance(response, dict):
                raw = response.get("models") or []
            else:
                raw = getattr(response, "models", None) or []
            names = []
            for m in raw:
                if isinstance(m, dict):
                    n = m.get("name") or m.get("model") or ""
                else:
                    n = (
                        getattr(m, "model", None)
                        or getattr(m, "name", None)
                        or ""
                    )
                if n:
                    names.append(str(n))
            return names
        except Exception:
            logger.exception("Ollama list_models failed")
            return []

    def ensure_model(self, name: str | None = None) -> bool:
        target = (name or self.model).strip()
        target_base = target.split(":")[0]
        for m in self.list_models():
            m = m.strip()
            if m == target or m.split(":")[0] == target_base:
                return True
        return False

    # ---- Chat (non-streaming) ----
    def chat(self, messages: list[dict], tools: list | None = None) -> dict:
        kwargs = {"model": self.model, "messages": messages}
        if tools:
            kwargs["tools"] = tools
        return self._client.chat(**kwargs)

    # ---- Chat (streaming, yields raw chunks) ----
    def stream_chat(self, messages: list[dict]):
        for chunk in self._client.chat(model=self.model, messages=messages, stream=True):
            yield chunk

    # ---- Embeddings ----
    def embed(self, text: str) -> list[float]:
        response = self._client.embeddings(model=self.embed_model, prompt=text)
        return response["embedding"]


_client_singleton: AssistantClient | None = None


def get_client() -> AssistantClient:
    global _client_singleton
    if _client_singleton is None:
        _client_singleton = AssistantClient()
    return _client_singleton