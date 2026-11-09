import ollama
from django.conf import settings

OLLAMA_HOST = getattr(settings, "OLLAMA_HOST", "http://ollama:11434")
OLLAMA_MODEL = getattr(settings, "OLLAMA_MODEL", "llama3.2:1b")

client = ollama.Client(host=OLLAMA_HOST)

def generate_stream(messages):
    """Comunica com o Ollama e devolve a resposta em stream."""
    try:
        stream = client.chat(model=OLLAMA_MODEL, messages=messages, stream=True)
        for chunk in stream:
            yield {"message": {"content": chunk['message']['content']}}
    except Exception as e:
        yield {"error": str(e)}