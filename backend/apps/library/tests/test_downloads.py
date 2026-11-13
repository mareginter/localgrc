import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.core.models import Organization, Role, UserRole
from apps.library.models import DocumentTemplate


@pytest.mark.django_db
def test_template_download_uses_private_internal_redirect(
    client, user, org, settings, tmp_path
):
    settings.MEDIA_ROOT = tmp_path
    template = DocumentTemplate.objects.create(
        organization=org,
        title="Security policy template",
        category="policy",
        file=SimpleUploadedFile(
            "policy-template.docx",
            b"test document",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
        uploaded_by=user,
    )
    client.force_login(user)

    response = client.get(reverse("template_download", kwargs={"pk": template.pk}))

    assert response.status_code == 200
    assert response["X-Accel-Redirect"].startswith("/uploads/library_templates/")
    assert response["Content-Disposition"].startswith("attachment;")
    assert response["Cache-Control"] == "private, no-store"
    assert response["X-Content-Type-Options"] == "nosniff"


@pytest.mark.django_db
def test_template_download_is_scoped_to_active_organization(
    client, user, org, settings, tmp_path
):
    settings.MEDIA_ROOT = tmp_path
    template = DocumentTemplate.objects.create(
        organization=org,
        title="Private template",
        category="policy",
        file=SimpleUploadedFile("private.docx", b"private document"),
        uploaded_by=user,
    )
    other_org = Organization.objects.create(name="Other", slug="library-download-other")
    other_user = type(user).objects.create_user(
        email="library-reader-other@test.local", password="pass1234word!"
    )
    UserRole.objects.create(
        user=other_user,
        role=Role.objects.get(code="reader"),
        organization=other_org,
    )
    client.force_login(other_user)

    response = client.get(reverse("template_download", kwargs={"pk": template.pk}))

    assert response.status_code == 404
