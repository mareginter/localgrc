import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.core.access import get_active_organization, require_org_roles

from . import rag
from .client import generate_stream, get_client
from .models import Document, DocumentChunk
from .tools import TOOL_DEFINITIONS, ToolExecutor

logger = logging.getLogger(__name__)
MAX_MESSAGE_CHARS = 8000
MAX_HISTORY_ITEMS = 10
MAX_DOCUMENT_BYTES = 20 * 1024 * 1024


@login_required
def assistant_home(request):
    get_active_organization(request)
    return render(request, "assistant/home.html")


@login_required
def assistant_health(request):
    get_active_organization(request)
    client = get_client()
    available = client.is_available()
    models = client.list_models() if available else []
    return JsonResponse({
        "available": available,
        "host": client.host,
        "configured_model": client.model,
        "models_installed": models,
        "model_ready": client.ensure_model() if available else False,
        "tools_available": len(TOOL_DEFINITIONS),
    })


@login_required
@require_POST
def assistant_stream(request):
    organization = get_active_organization(request)
    try:
        data = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON request."}, status=400)

    if not isinstance(data, dict):
        return JsonResponse({"error": "Invalid request payload."}, status=400)

    user_message = data.get("message")
    history = data.get("history", [])
    use_tools = data.get("use_tools", True)

    if not isinstance(user_message, str) or not user_message.strip():
        return JsonResponse({"error": "A message is required."}, status=400)
    if len(user_message) > MAX_MESSAGE_CHARS:
        return JsonResponse({"error": "Message exceeds the allowed length."}, status=413)
    if not isinstance(history, list) or len(history) > MAX_HISTORY_ITEMS:
        return JsonResponse({"error": "Invalid conversation history."}, status=400)

    validated_history = []
    for item in history:
        if not isinstance(item, dict):
            return JsonResponse({"error": "Invalid conversation history."}, status=400)
        role = item.get("role")
        content = item.get("content")
        if role not in {"user", "assistant"} or not isinstance(content, str):
            return JsonResponse({"error": "Invalid conversation history."}, status=400)
        if len(content) > MAX_MESSAGE_CHARS:
            return JsonResponse({"error": "Conversation history item is too long."}, status=413)
        validated_history.append({"role": role, "content": content})

    # 1. RAG Context retrieval (Original logic)
    context = rag.search_context(user_message, organization)
    system_prompt = (
        "És um assistente GRC especialista. Responde de forma profissional e clara em português. "
        "Tens acesso a ferramentas (tools) que consultam a base de dados em tempo real. "
        "Usa essas ferramentas SEMPRE que a pergunta envolver riscos, controlos, políticas, "
        "auditorias, incidentes ou vulnerabilidades. Não inventes dados."
    )
    if context:
        system_prompt += (
            "\n\nUsa o seguinte CONTEXTO extraído dos documentos disponíveis para responder. "
            "Se a resposta não estiver no contexto, diz que não sabes.\n\nCONTEXTO:\n" + context
        )

    chat_messages = [{"role": "system", "content": system_prompt}]
    chat_messages.extend(validated_history)
    chat_messages.append({"role": "user", "content": user_message.strip()})

    def event_stream():
        client = get_client()

        # 2. Tool Loop (Nova lógica)
        if use_tools and organization:
            try:
                executor = ToolExecutor(organization, request.user)
                for _ in range(5):  # max iterations
                    response = client.chat_with_tools(chat_messages, TOOL_DEFINITIONS)
                    
                    # Normalize SDK response (dict or Pydantic)
                    if isinstance(response, dict):
                        msg = response.get("message", {})
                    else:
                        msg = getattr(response, "message", None)
                        if hasattr(msg, "model_dump"):
                            msg = msg.model_dump()
                        elif msg is None:
                            msg = {}

                    tool_calls = msg.get("tool_calls", [])
                    if not tool_calls:
                        break

                    # Append assistant's intention to call tools
                    chat_messages.append(msg)
                    print(f"--- OLLAMA REQUESTED TOOLS: {tool_calls}", flush=True)

                    for tc in tool_calls:
                        # Parse tool call data
                        fn = tc.get("function", {}) if isinstance(tc, dict) else getattr(tc, "function", {})
                        name = fn.get("name") if isinstance(fn, dict) else getattr(fn, "name", "")
                        args = fn.get("arguments") if isinstance(fn, dict) else getattr(fn, "arguments", {})
                        
                        if isinstance(args, str):
                            try: args = json.loads(args)
                            except json.JSONDecodeError: args = {}

                        yield f"data: {json.dumps({'status': f'A consultar dados: {name}...'})}\n\n"
                        
                        # Execute tool
                        result = executor.execute(name, args)
                        
                        print(f"--- TOOL RESULT: {result}", flush=True)
                        
                        # Feed result back to model
                        chat_messages.append({
                            "role": "tool",
                            "content": result,
                            "name": name
                        })
            except Exception:
                logger.exception("Tool loop failed for user %s", request.user.pk)
                yield f"data: {json.dumps({'error': 'The assistant could not query the database.'})}\n\n"
                return

        # 3. Stream Final Answer
        try:
            for chunk in generate_stream(chat_messages):
                if "message" in chunk and "content" in chunk["message"]:
                    delta = chunk["message"]["content"]
                    yield f"data: {json.dumps({'delta': delta})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception:
            logger.exception("Assistant stream failed for user %s", request.user.pk)
            yield f"data: {json.dumps({'error': 'The assistant could not complete the request.'})}\n\n"

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["X-Accel-Buffering"] = "no"
    return response


@login_required
@require_org_roles("admin")
@require_POST
def document_upload(request):
    organization = get_active_organization(request)
    file = request.FILES.get("document")
    if not file:
        messages.error(request, "Select a PDF document to upload.")
        return redirect("assistant_home")
    if file.size > MAX_DOCUMENT_BYTES:
        messages.error(request, "The PDF exceeds the 20 MB upload limit.")
        return redirect("assistant_home")
    if not file.name.lower().endswith(".pdf"):
        messages.error(request, "Only PDF documents are accepted.")
        return redirect("assistant_home")
    try:
        signature = file.read(5)
        file.seek(0)
        if signature != b"%PDF-":
            messages.error(request, "The uploaded file is not a valid PDF document.")
            return redirect("assistant_home")

        doc = Document.objects.create(title=file.name[:255], file=file, organization=organization, uploaded_by=request.user)
        text = rag.extract_text_from_pdf(doc.file)
        if not text.strip():
            doc.delete()
            messages.error(request, "No readable text could be extracted from the PDF.")
            return redirect("assistant_home")

        chunks = rag.chunk_text(text)
        for chunk_text in chunks:
            embedding = rag.get_embedding(chunk_text)
            if embedding:
                DocumentChunk.objects.create(document=doc, text=chunk_text, embedding=embedding)
        messages.success(request, f"Document '{file.name}' processed successfully.")
    except Exception:
        logger.exception("PDF upload or processing failed for user %s", request.user.pk)
        messages.error(request, "The PDF could not be processed. Check the server logs.")
    return redirect("assistant_home")