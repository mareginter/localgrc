"""Tests for RegulatoryDeadline model + auto-creation."""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.core.models import Organization


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Test Org", slug="test-org")


@pytest.mark.django_db
def test_gdpr_deadline_auto_created_for_data_breach(org):
    from apps.incidents.models import Incident, RegulatoryDeadline, ensure_regulatory_deadlines

    incident = Incident.objects.create(
        organization=org, title="Data breach", category="data_breach"
    )
    ensure_regulatory_deadlines(incident)

    assert RegulatoryDeadline.objects.filter(
        incident=incident, regulation="gdpr_72h"
    ).exists()


@pytest.mark.django_db
def test_deadline_is_overdue_after_passing(org):
    from apps.incidents.models import Incident, RegulatoryDeadline

    incident = Incident.objects.create(
        organization=org, title="Breach", category="data_breach"
    )
    d = RegulatoryDeadline.objects.create(
        incident=incident,
        regulation="gdpr_72h",
        deadline_at=timezone.now() - timedelta(hours=1),
    )
    assert d.is_overdue is True


@pytest.mark.django_db
def test_deadline_not_overdue_if_notified(org):
    from apps.incidents.models import Incident, RegulatoryDeadline

    incident = Incident.objects.create(
        organization=org, title="Breach", category="data_breach"
    )
    d = RegulatoryDeadline.objects.create(
        incident=incident,
        regulation="gdpr_72h",
        deadline_at=timezone.now() - timedelta(hours=1),
        notified_at=timezone.now() - timedelta(hours=2),
    )
    assert d.is_overdue is False