import pytest
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory

from apps.core.access import get_active_organization, ACTIVE_ORGANIZATION_SESSION_KEY
from apps.core.models import Organization, Role, UserRole


def test_single_membership_is_selected_automatically(rf, user, org):
    request = rf.get("/")
    request.user = user
    request.session = {}
    assert get_active_organization(request) == org
    assert request.session[ACTIVE_ORGANIZATION_SESSION_KEY] == str(org.pk)


def test_invalid_active_organization_falls_back_to_valid_membership(rf, user, org):
    other = Organization.objects.create(name="Other", slug="other")
    request = rf.get("/")
    request.user = user
    request.session = {ACTIVE_ORGANIZATION_SESSION_KEY: str(other.pk)}
    assert get_active_organization(request) == org
    assert request.session[ACTIVE_ORGANIZATION_SESSION_KEY] == str(org.pk)


def test_multiple_memberships_default_to_first_sorted_organization(rf, user, org):
    other = Organization.objects.create(name="Other", slug="other")
    UserRole.objects.create(user=user, role=Role.objects.get(code="reader"), organization=other)
    request = rf.get("/")
    request.user = user
    request.session = {}
    assert get_active_organization(request) == other


def test_explicit_member_selection_is_accepted(rf, user, org):
    other = Organization.objects.create(name="Other", slug="other")
    UserRole.objects.create(user=user, role=Role.objects.get(code="reader"), organization=other)
    request = rf.get("/")
    request.user = user
    request.session = {ACTIVE_ORGANIZATION_SESSION_KEY: str(other.pk)}
    assert get_active_organization(request) == other


def test_user_with_no_membership_is_denied(client, db):
    from django.contrib.auth import get_user_model
    outsider = get_user_model().objects.create_user(email="outsider@test.local", password="pass1234word!")
    client.force_login(outsider)
    assert client.get("/").status_code == 403


def test_organization_switch_rejects_non_member(client, user, org):
    other = Organization.objects.create(name="Other", slug="other")
    client.force_login(user)
    response = client.post("/organization/switch/", {"organization_id": str(other.pk)})
    assert response.status_code == 403


def test_reader_cannot_create_risk(client, db):
    from django.contrib.auth import get_user_model
    reader = get_user_model().objects.create_user(email="reader@test.local", password="pass1234word!")
    org = Organization.objects.create(name="Reader Org", slug="reader-org")
    UserRole.objects.create(user=reader, role=Role.objects.get(code="reader"), organization=org)
    client.force_login(reader)
    response = client.post("/risks/new/", {})
    assert response.status_code == 403


def test_organization_switch_accepts_member(client, user, org):
    other = Organization.objects.create(name="Other", slug="other")
    UserRole.objects.create(user=user, role=Role.objects.get(code="reader"), organization=other)
    client.force_login(user)
    response = client.post("/organization/switch/", {"organization_id": str(other.pk)})
    assert response.status_code == 302
    assert client.session[ACTIVE_ORGANIZATION_SESSION_KEY] == str(other.pk)


def test_tenant_scoped_forms_only_offer_same_org_users(db, user, org):
    from django.contrib.auth import get_user_model
    from apps.risks.forms import RiskForm
    other_org = Organization.objects.create(name="Other", slug="other")
    other_user = get_user_model().objects.create_user(
        email="other-user@test.local", password="pass1234word!"
    )
    UserRole.objects.create(
        user=other_user, role=Role.objects.get(code="contributor"), organization=other_org
    )
    form = RiskForm(organization=org)
    owner_ids = set(form.fields["owner"].queryset.values_list("pk", flat=True))
    assert user.pk in owner_ids
    assert other_user.pk not in owner_ids


@pytest.mark.parametrize(
    "path",
    [
        "/users/new/",
        "/risks/new/",
        "/risks/assets/new/",
        "/controls/new/",
        "/audits/new/",
        "/incidents/new/",
        "/evidence/new/",
        "/policies/new/",
        "/vendors/new/",
        "/vulnerabilities/new/",
        "/library/new/",
        "/assistant/upload/",
    ],
)
def test_reader_cannot_post_to_protected_create_endpoints(client, org, path):
    from django.contrib.auth import get_user_model

    reader = get_user_model().objects.create_user(
        email=f"reader-{path.strip('/').replace('/', '-') or 'root'}@test.local",
        password="pass1234word!",
    )
    UserRole.objects.create(
        user=reader,
        role=Role.objects.get(code="reader"),
        organization=org,
    )
    client.force_login(reader)

    response = client.post(path, {})

    assert response.status_code == 403, f"Reader unexpectedly accessed {path}"
