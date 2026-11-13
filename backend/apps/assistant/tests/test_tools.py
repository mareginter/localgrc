"""Tests for assistant tool calling — verify tenant isolation and logic."""

import json

import pytest

from apps.core.models import Organization


@pytest.fixture
def org_a(db):
    return Organization.objects.create(name="Org A", slug="org-a")


@pytest.fixture
def org_b(db):
    return Organization.objects.create(name="Org B", slug="org-b")


@pytest.fixture
def user(db):
    from apps.core.models import User
    return User.objects.create_user(email="user@test.local", password="test1234!")


@pytest.mark.django_db
def test_list_risks_isolated_by_org(org_a, org_b, user):
    from apps.risks.models import Risk
    from apps.assistant.tools import ToolExecutor

    Risk.objects.create(organization=org_a, title="Risk A")
    Risk.objects.create(organization=org_b, title="Risk B")

    executor = ToolExecutor(org_a, user)
    result = json.loads(executor.execute("list_risks", {}))
    assert result["count"] == 1
    assert result["risks"][0]["title"] == "Risk A"


@pytest.mark.django_db
def test_framework_coverage_computed(org_a, user):
    from apps.frameworks.models import Framework, FrameworkVersion, Requirement
    from apps.controls.models import Control, ControlRequirement
    from apps.assistant.tools import ToolExecutor

    fw = Framework.objects.create(organization=org_a, code="iso27001", name="ISO 27001")
    fv = FrameworkVersion.objects.create(framework=fw, version="2022", is_active=True)
    r1 = Requirement.objects.create(framework_version=fv, code="A.1", title="R1", order=1)
    r2 = Requirement.objects.create(framework_version=fv, code="A.2", title="R2", order=2)
    ctrl = Control.objects.create(organization=org_a, name="C")
    ControlRequirement.objects.create(control=ctrl, requirement=r1, coverage="full")

    executor = ToolExecutor(org_a, user)
    result = json.loads(executor.execute("framework_coverage", {"framework_code": "iso27001"}))
    assert result["total_requirements"] == 2
    assert result["fully_covered"] == 1
    assert result["coverage_pct"] == 50


@pytest.mark.django_db
def test_unknown_tool_returns_error(org_a, user):
    from apps.assistant.tools import ToolExecutor

    executor = ToolExecutor(org_a, user)
    result = json.loads(executor.execute("nonexistent_tool", {}))
    assert "error" in result