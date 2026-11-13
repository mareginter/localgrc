import pytest
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.core.models import Organization, Role, UserRole
from apps.evidence.models import Evidence


@pytest.mark.django_db
def test_collector_cannot_verify_own_evidence(client, user, org):
    evidence = Evidence.objects.create(
        organization=org,
        title="Evidence collected by current user",
        content_type=ContentType.objects.get_for_model(Organization),
        object_id=org.pk,
        collected_by=user,
    )
    client.force_login(user)

    response = client.post(
        reverse("evidence_verify", kwargs={"pk": evidence.pk}),
        {"notes": "Self verification attempt"},
    )

    evidence.refresh_from_db()
    assert response.status_code == 302
    assert evidence.verified_at is None
    assert evidence.verified_by_id is None


@pytest.mark.django_db
def test_another_authorized_user_can_verify_evidence(client, user, org):
    evidence = Evidence.objects.create(
        organization=org,
        title="Evidence awaiting independent verification",
        content_type=ContentType.objects.get_for_model(Organization),
        object_id=org.pk,
        collected_by=user,
    )
    verifier = get_user_model().objects.create_user(
        email="independent-verifier@test.local",
        password="pass1234word!",
    )
    UserRole.objects.create(
        user=verifier,
        role=Role.objects.get(code="admin"),
        organization=org,
    )
    client.force_login(verifier)

    response = client.post(
        reverse("evidence_verify", kwargs={"pk": evidence.pk}),
        {"notes": "Reviewed and accepted"},
    )

    evidence.refresh_from_db()
    assert response.status_code == 302
    assert evidence.verified_by_id == verifier.pk
    assert evidence.verified_at is not None
    assert evidence.verification_notes == "Reviewed and accepted"


@pytest.mark.django_db
def test_evidence_verification_rejects_get(client, user, org):
    evidence = Evidence.objects.create(
        organization=org,
        title="GET must not change verification state",
        content_type=ContentType.objects.get_for_model(Organization),
        object_id=org.pk,
        collected_by=None,
    )
    client.force_login(user)

    response = client.get(reverse("evidence_verify", kwargs={"pk": evidence.pk}))

    evidence.refresh_from_db()
    assert response.status_code == 405
    assert evidence.verified_at is None
    assert evidence.verified_by_id is None
