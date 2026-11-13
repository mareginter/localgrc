"""Tests for Control model business logic."""

from datetime import date

import pytest

from apps.core.models import Organization


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Test Org", slug="test-org")


@pytest.mark.django_db
def test_control_auto_code_increments(org):
    from apps.controls.models import Control

    c1 = Control.objects.create(organization=org, name="Control A")
    c2 = Control.objects.create(organization=org, name="Control B")

    assert c1.code == "CTL-0001"
    assert c2.code == "CTL-0002"


@pytest.mark.django_db
def test_control_implementation_unique_per_department(org):
    from django.db import IntegrityError
    from apps.controls.models import Control, ControlImplementation

    ctrl = Control.objects.create(organization=org, name="Ctrl")
    ControlImplementation.objects.create(control=ctrl, department="IT", status="implemented")

    with pytest.raises(IntegrityError):
        ControlImplementation.objects.create(
            control=ctrl, department="IT", status="not_implemented"
        )


@pytest.mark.django_db
def test_coverage_full_partial_na_counted_separately(org):
    from apps.frameworks.models import Framework, FrameworkVersion, Requirement
    from apps.controls.models import Control, ControlRequirement

    fw = Framework.objects.create(organization=org, code="testfw", name="Test FW")
    fv = FrameworkVersion.objects.create(framework=fw, version="1.0", is_active=True)
    r1 = Requirement.objects.create(framework_version=fv, code="A.1", title="Req 1", order=1)
    r2 = Requirement.objects.create(framework_version=fv, code="A.2", title="Req 2", order=2)
    r3 = Requirement.objects.create(framework_version=fv, code="A.3", title="Req 3", order=3)

    ctrl = Control.objects.create(organization=org, name="Coverage Control")
    ControlRequirement.objects.create(control=ctrl, requirement=r1, coverage="full")
    ControlRequirement.objects.create(control=ctrl, requirement=r2, coverage="partial")
    ControlRequirement.objects.create(control=ctrl, requirement=r3, coverage="na")

    links = ControlRequirement.objects.filter(control=ctrl)
    assert links.filter(coverage="full").count() == 1
    assert links.filter(coverage="partial").count() == 1
    assert links.filter(coverage="na").count() == 1
    assert links.count() == 3