"""Tests for CorrectiveAction model business logic."""

import pytest

from apps.core.models import Organization


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Test Org", slug="test-org")


@pytest.fixture
def finding(db, org):
    from apps.audits.models import Audit, AuditFinding

    audit = Audit.objects.create(organization=org, title="Test Audit")
    return AuditFinding.objects.create(
        audit=audit, title="Finding", severity="minor_nc", status="open"
    )


@pytest.mark.django_db
def test_corrective_action_completed_at_auto_set(finding):
    from apps.audits.models import CorrectiveAction

    ca = CorrectiveAction.objects.create(
        finding=finding, description="Fix it", status="completed"
    )
    assert ca.completed_at is not None


@pytest.mark.django_db
def test_corrective_action_completed_at_not_set_if_planned(finding):
    from apps.audits.models import CorrectiveAction

    ca = CorrectiveAction.objects.create(
        finding=finding, description="Plan it", status="planned"
    )
    assert ca.completed_at is None


@pytest.mark.django_db
def test_corrective_action_verified_by_set(finding):
    from django.utils import timezone
    from apps.audits.models import CorrectiveAction
    from apps.core.models import User

    user = User.objects.create_user(email="auditor@test.local", password="test1234!")
    ca = CorrectiveAction.objects.create(
        finding=finding, description="Verified fix", status="verified",
        verified_by=user, verified_at=timezone.now(),
    )
    assert ca.verified_by == user
    assert ca.verified_at is not None