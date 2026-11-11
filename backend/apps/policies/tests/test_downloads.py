import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.policies.models import Policy, PolicyVersion


@pytest.mark.django_db
def test_policy_version_download_uses_private_internal_redirect(
    client, user, org, settings, tmp_path
):
    settings.MEDIA_ROOT = tmp_path
    policy = Policy.objects.create(organization=org, title="Access control policy")
    version = PolicyVersion.objects.create(
        policy=policy,
        version_number=1,
        file_attachment=SimpleUploadedFile(
            "policy.pdf", b"%PDF-1.4 test", content_type="application/pdf"
        ),
    )
    client.force_login(user)

    response = client.get(
        reverse(
            "policy_version_download",
            kwargs={"pk": policy.pk, "version_pk": version.pk},
        )
    )

    assert response.status_code == 200
    assert response["X-Accel-Redirect"].startswith("/uploads/policies/")
    assert response["Content-Disposition"].startswith("attachment;")


@pytest.mark.django_db
def test_policy_version_download_is_scoped_to_active_organization(
    client, org, settings, tmp_path
):
    from django.contrib.auth import get_user_model
    from apps.core.models import Organization, Role, UserRole

    settings.MEDIA_ROOT = tmp_path
    policy = Policy.objects.create(organization=org, title="Private policy")
    version = PolicyVersion.objects.create(
        policy=policy,
        version_number=1,
        file_attachment=SimpleUploadedFile("policy.pdf", b"%PDF-1.4 test"),
    )
    other_org = Organization.objects.create(name="Other", slug="policy-download-other")
    other_user = get_user_model().objects.create_user(
        email="policy-reader-other@test.local", password="pass1234word!"
    )
    UserRole.objects.create(
        user=other_user, role=Role.objects.get(code="reader"), organization=other_org
    )
    client.force_login(other_user)

    response = client.get(
        reverse(
            "policy_version_download",
            kwargs={"pk": policy.pk, "version_pk": version.pk},
        )
    )

    assert response.status_code == 404
