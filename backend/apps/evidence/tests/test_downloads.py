import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.core.models import Organization, Role, UserRole
from apps.evidence.models import Evidence


@pytest.mark.django_db
def test_evidence_download_uses_private_internal_redirect(
    client, user, org, settings, tmp_path
):
    settings.MEDIA_ROOT = tmp_path
    evidence = Evidence.objects.create(
        organization=org,
        title="Security evidence",
        content_type=ContentType.objects.get_for_model(Organization),
        object_id=org.pk,
        attachment=SimpleUploadedFile(
            "proof.pdf", b"%PDF-1.4 test", content_type="application/pdf"
        ),
    )
    client.force_login(user)

    response = client.get(reverse("evidence_download", kwargs={"pk": evidence.pk}))

    assert response.status_code == 200
    assert response["X-Accel-Redirect"].startswith("/uploads/evidence/")
    assert response["Content-Disposition"].startswith("attachment;")
    assert response["Cache-Control"] == "private, no-store"


@pytest.mark.django_db
def test_evidence_download_is_scoped_to_active_organization(
    client, org, settings, tmp_path
):
    from django.contrib.auth import get_user_model

    settings.MEDIA_ROOT = tmp_path
    evidence = Evidence.objects.create(
        organization=org,
        title="Private evidence",
        content_type=ContentType.objects.get_for_model(Organization),
        object_id=org.pk,
        attachment=SimpleUploadedFile("proof.pdf", b"%PDF-1.4 test"),
    )
    other_org = Organization.objects.create(name="Other", slug="download-other")
    other_user = get_user_model().objects.create_user(
        email="reader-other@test.local", password="pass1234word!"
    )
    UserRole.objects.create(
        user=other_user,
        role=Role.objects.get(code="reader"),
        organization=other_org,
    )
    client.force_login(other_user)

    response = client.get(reverse("evidence_download", kwargs={"pk": evidence.pk}))

    assert response.status_code == 404
