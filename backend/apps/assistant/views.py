import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .client import get_client


@login_required
def assistant_home(request):
    return render(request, "assistant/home.html")


@login_required
@require_GET
def assistant_health(request):
    client = get_client()
    available = client.is_available()
    models = client.list_models() if available else []
    return JsonResponse({
        "available": available,
        "host": client.host,
        "configured_model": client.model,
        "models_installed": models,
        "model_ready": client.ensure_model() if available else False,
    })


@login_required
@require_POST
def assistant_stream(request):
    """SSE endpoint: streams the assistant's reply token by token."""
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "invalid JSON"}, status=400)

    user_message = (payload.get("message") or "").strip()
    history = payload.get("history") or []
    if not user_message:
        return JsonResponse({"error": "message is required"}, status=400)

    system = (
        "You are the LocalGRC assistant, embedded in a Governance, Risk and "
        "Compliance platform that runs entirely on the user's LAN. "
        "Answer concisely in the user's language. When you are not sure about "
        "internal data, say so explicitly and suggest which section of the "
        "platform to check (Risks, Controls, Policies, Audits, Vendors, "
        "Incidents, Evidence)."
    )

    messages = [{"role": "system", "content": system}]
    for m in history[-20:]:
        role = m.get("role")
        content = m.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_message})

    client = get_client()

    def event_stream():
        try:
            for chunk in client.stream_chat(messages):
                content = ""
                if isinstance(chunk, dict):
                    message = chunk.get("message") or {}
                    content = message.get("content") or ""
                else:
                    message = getattr(chunk, "message", None)
                    content = getattr(message, "content", "") if message else ""
                if content:
                    yield f"data: {json.dumps({'delta': content})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"  # tell nginx not to buffer
    return response