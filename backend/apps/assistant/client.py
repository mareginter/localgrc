"""Ollama client wrapper. All Ollama-specific logic lives here."""

import logging

import ollama
from django.conf import settings

logger = logging.getLogger(__name__)


class AssistantClient:
    def __init__(self):
        self.host = getattr(settings, "OLLAMA_HOST", "http://ollama:11434")
        self.model = getattr(settings, "OLLAMA_MODEL", "llama3.1:8b")
        self.embed_model = getattr(settings, "OLLAMA_EMBED_MODEL", "nomic-embed-text")
        self.timeout = getattr(settings, "OLLAMA_TIMEOUT", 300)
        self._client = ollama.Client(host=self.host, timeout=self.timeout)

    def is_available(self) -> bool:
        try:
            self._client.list()
            return True
        except Exception:
            logger.exception("Ollama unavailable")
            return False

    def list_models(self) -> list[str]:
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
                    n = getattr(m, "model", None) or getattr(m, "name", None) or ""
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

    def chat(self, messages, tools=None):
        kwargs = {"model": self.model, "messages": messages, "think": False}
        if tools:
            kwargs["tools"] = tools
        return self._client.chat(**kwargs)

    def chat_with_tools(self, messages, tools):
        """Non-streaming chat with tools (used by tool loop)."""
        return self._client.chat(
            model=self.model,
            messages=messages,
            tools=tools,
            stream=False,
            think=False,
        )

    def stream_chat(self, messages):
        """Yields raw chunks from ollama SDK."""
        for chunk in self._client.chat(
            model=self.model, messages=messages, stream=True, think=False
        ):
            yield chunk

    def embed(self, text: str) -> list[float]:
        response = self._client.embeddings(model=self.embed_model, prompt=text)
        return response["embedding"]


_client_singleton = None


def get_client() -> AssistantClient:
    global _client_singleton
    if _client_singleton is None:
        _client_singleton = AssistantClient()
    return _client_singleton

def generate_stream(messages):
    """Backwards-compatible wrapper expected by views.py.

    Receives a list of chat messages and yields dicts of the form
    {"message": {"content": "..."}} or {"error": "..."}.
    """
    client = get_client()
    try:
        for chunk in client.stream_chat(messages):
            content = ""
            if isinstance(chunk, dict):
                content = (chunk.get("message") or {}).get("content", "")
            else:
                msg = getattr(chunk, "message", None)
                content = getattr(msg, "content", "") if msg else ""
            if content:
                yield {"message": {"content": content}}
    except Exception as e:
        yield {"error": str(e)}
