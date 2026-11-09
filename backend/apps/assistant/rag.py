import numpy as np
from pypdf import PdfReader
import ollama
from django.conf import settings

OLLAMA_HOST = getattr(settings, "OLLAMA_HOST", "http://ollama:11434")
OLLAMA_EMBED_MODEL = getattr(settings, "OLLAMA_EMBED_MODEL", "nomic-embed-text")

client = ollama.Client(host=OLLAMA_HOST)

def chunk_text(text, chunk_size=800, overlap=100):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks

def get_embedding(text):
    """Pede ao Ollama para converter texto num vetor (embedding)."""
    try:
        # Tenta a API moderna
        if hasattr(client, 'embed'):
            response = client.embed(model=OLLAMA_EMBED_MODEL, input=text)
            return response['embeddings'][0]
        # Tenta a API antiga
        else:
            response = client.embeddings(model=OLLAMA_EMBED_MODEL, prompt=text)
            return response['embedding']
    except Exception as e:
        print(f"!!! ERRO OLLAMA EMBEDDING: {e}")
        return None

def extract_text_from_pdf(file_field):
    try:
        reader = PdfReader(file_field)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text
    except Exception as e:
        print(f"!!! ERRO AO LER PDF: {e}")
        return ""

def cosine_similarity(v1, v2):
    if not v1 or not v2:
        return 0
    a = np.array(v1)
    b = np.array(v2)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def search_context(query, top_k=3):
    from .models import DocumentChunk
    query_embedding = get_embedding(query)
    if not query_embedding:
        return ""

    chunks = DocumentChunk.objects.all()
    if not chunks:
        return ""

    scored_chunks = []
    for chunk in chunks:
        score = cosine_similarity(query_embedding, chunk.embedding)
        scored_chunks.append((score, chunk.text))

    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    context = "\n\n---\n\n".join([text for score, text in scored_chunks[:top_k] if score > 0.3])
    return context