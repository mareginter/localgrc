"""Tests for Vendor model + dashboard query."""

from datetime import date, timedelta

import pytest

from apps.core.models import Organization


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Test Org", slug="test-org")


@pytest.mark.django_db
def test_vendor_critical_no_dpa_query_returns_only_those(org):
    from apps.vendors.models import Vendor

    v_no_dpa = Vendor.objects.create(
        organization=org, name="V no DPA", criticality="critical", dpa_signed=False
    )
    Vendor.objects.create(
        organization=org, name="V with DPA", criticality="critical", dpa_signed=True
    )
    Vendor.objects.create(
        organization=org, name="Low no DPA", criticality="low", dpa_signed=False
    )

    qs = Vendor.objects.filter(
        organization=org, criticality__in=["high", "critical"], dpa_signed=False
    )
    assert list(qs) == [v_no_dpa]


@pytest.mark.django_db
def test_vendor_assessment_ordering_desc(org):
    from apps.vendors.models import Vendor, VendorAssessment

    v = Vendor.objects.create(organization=org, name="Vendor")
    a_old = VendorAssessment.objects.create(
        vendor=v, assessment_date=date.today() - timedelta(days=30), score=50
    )
    a_new = VendorAssessment.objects.create(
        vendor=v, assessment_date=date.today(), score=80
    )
    assessments = list(v.assessments.all())
    assert assessments[0] == a_new  # most recent first
    assert assessments[1] == a_old