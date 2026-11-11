"""Regression tests for read-only RBAC enforcement across mutation endpoints."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.core.models import Role, UserRole


MUTATING_ENDPOINTS = [
    ("risk_create", {}),
    ("risk_update", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("assessment_create", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("treatment_create", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("asset_create", {}),
    ("control_create", {}),
    ("control_update", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("requirement_link_create", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("implementation_create", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("control_transition", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("policy_create", {}),
    ("policy_update", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("version_create", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("policy_approve", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("policy_transition", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("audit_create", {}),
    ("audit_update", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("audit_transition", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("finding_create", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("finding_update", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("finding_transition", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("action_create", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("action_verify", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("incident_create", {}),
    ("incident_update", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("incident_transition", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("deadline_create", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("deadline_mark_notified", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("incident_risk_link_create", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("incident_vendor_link_create", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("incident_asset_link_create", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("vendor_create", {}),
    ("vendor_update", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("vendor_assessment_create", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("vendor_risk_link_create", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("vendor_control_link_create", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("vendor_transition", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("evidence_create", {}),
    ("evidence_update", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("evidence_verify", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("vuln_create", {}),
    ("vuln_update", {"pk": "11111111-1111-4111-8111-111111111111"}),
    ("template_create", {}),
    ("document_upload", {}),
    ("user_create", {}),
    ("user_update", {"pk": "11111111-1111-4111-8111-111111111111"}),
]


@pytest.mark.django_db
@pytest.mark.parametrize("route_name,kwargs", MUTATING_ENDPOINTS)
def test_reader_cannot_post_to_mutation_endpoints(client, org, route_name, kwargs):
    """A Reader must be rejected before any mutation view processes its payload."""
    user_model = get_user_model()
    reader = user_model.objects.create_user(
        email=f"reader-{route_name}@test.local",
        password="Strong-Test-Password-2026!",
    )
    UserRole.objects.create(
        user=reader,
        role=Role.objects.get(code="reader"),
        organization=org,
    )
    client.force_login(reader)

    response = client.post(reverse(route_name, kwargs=kwargs), {})

    assert response.status_code == 403, (
        f"Reader unexpectedly reached mutation endpoint {route_name}; "
        f"received HTTP {response.status_code}."
    )
