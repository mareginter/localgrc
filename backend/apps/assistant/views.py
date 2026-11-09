import json
from django.shortcuts import render, redirect
from django.http import JsonResponse, StreamingHttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from . import rag
from .models import Document, DocumentChunk
from .client import generate_stream

@login_required
def assistant_home(request):
    return render(request, "assistant/home.html")

@login_required
def assistant_health(request):
    # Health check básico
    return JsonResponse({"status": "ok"})

@login_required
@csrf_exempt
def assistant_stream(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_message = data.get("message", "")
        history = data.get("history", [])
        
        # Procura contexto nos PDFs carregados (RAG)
        context = rag.search_context(user_message)
        
        system_prompt = "És um assistente GRC especialista. Responde de forma profissional e clara em português."
        if context:
            system_prompt += f"\n\nUsa o seguinte CONTEXTO extraído dos documentos da organização para responder. Se a resposta não estiver no contexto, diz que não sabes.\n\nCONTEXTO:\n{context}"

        # Junta o histórico + system prompt + nova pergunta
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        def event_stream():
            try:
                for chunk in generate_stream(messages):
                    if "message" in chunk and "content" in chunk["message"]:
                        delta = chunk["message"]["content"]
                        yield f"data: {json.dumps({'delta': delta})}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingHttpResponse(event_stream(), content_type="text/event-stream")

@login_required
def document_upload(request):
    if request.method == 'POST':
        file = request.FILES.get('document')
        if file:
            try:
                doc = Document.objects.create(title=file.name, file=file)
                text = rag.extract_text_from_pdf(doc.file)
                chunks = rag.chunk_text(text)
                for c in chunks:
                    emb = rag.get_embedding(c)
                    if emb:
                        DocumentChunk.objects.create(document=doc, text=c, embedding=emb)
                messages.success(request, f"Documento '{file.name}' processado com sucesso!")
            except Exception as e:
                messages.error(request, f"Erro ao processar PDF: {e}")
        return redirect('assistant_home')
    return redirect('assistant_home')