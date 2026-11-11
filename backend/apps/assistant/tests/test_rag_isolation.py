import pytest
from django.test import Client
from django.urls import reverse

from apps.assistant import rag
from apps.assistant.models import Document, DocumentChunk
from apps.core.models import Organization, Role, UserRole


@pytest.mark.django_db
def test_rag_search_returns_only_chunks_from_active_organization(
    org, monkeypatch
):
    other_org = Organization.objects.create(name="Other", slug="rag-other-org")
    own_document = Document.objects.create(
        organization=org, title="Own document", file="rag/own.pdf"
    )
    other_document = Document.objects.create(
        organization=other_org, title="Other document", file="rag/other.pdf"
    )
    legacy_document = Document.objects.create(
        organization=None, title="Legacy document", file="rag/legacy.pdf"
    )
    DocumentChunk.objects.create(
        document=own_document, text="OWN_ORG_CONTENT", embedding=[1.0, 0.0]
    )
    DocumentChunk.objects.create(
        document=other_document, text="OTHER_ORG_CONTENT", embedding=[1.0, 0.0]
    )
    DocumentChunk.objects.create(
        document=legacy_document, text="LEGACY_UNASSIGNED_CONTENT", embedding=[1.0, 0.0]
    )
    monkeypatch.setattr(rag, "get_embedding", lambda _query: [1.0, 0.0])

    context = rag.search_context("test query", org)

    assert "OWN_ORG_CONTENT" in context
    assert "OTHER_ORG_CONTENT" not in context
    assert "LEGACY_UNASSIGNED_CONTENT" not in context


@pytest.mark.django_db
def test_assistant_stream_requires_csrf_token(user):
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)

    response = client.post(
        reverse("assistant_stream"),
        data='{"message":"test"}',
        content_type="application/json",
    )

    assert response.status_code == 403
