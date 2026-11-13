import pytest
from types import SimpleNamespace

from apps.core.workflows import _object_organization_id


def _tenant_root(organization_id, *, deleted_at=None):
    return SimpleNamespace(organization_id=organization_id, deleted_at=deleted_at)


def _workflow_object(label, **relations):
    return SimpleNamespace(
        _meta=SimpleNamespace(label_lower=label, get_fields=lambda: []),
        deleted_at=None,
        **relations,
    )


@pytest.mark.parametrize(
    ("label", "relation_name", "path"),
    [
        ("audits.auditfinding", "audit", ("audit",)),
        ("audits.correctiveaction", "finding", ("finding", "audit")),
        ("risks.riskassessment", "risk", ("risk",)),
        ("policies.policyversion", "policy", ("policy",)),
        ("incidents.regulatorydeadline", "incident", ("incident",)),
        ("controls.controlimplementation", "control", ("control",)),
        ("frameworks.frameworkversion", "framework", ("framework",)),
        ("frameworks.requirement", "framework_version", ("framework_version", "framework")),
    ],
)
def test_child_workflow_objects_resolve_tenant(label, relation_name, path):
    nested = _tenant_root(73)
    for name in reversed(path[1:]):
        nested = SimpleNamespace(**{name: nested})
    obj = _workflow_object(label, **{relation_name: nested})
    assert _object_organization_id(obj) == 73


def test_deleted_tenant_root_is_rejected():
    obj = _workflow_object("risks.riskassessment", risk=_tenant_root(73, deleted_at=object()))
    assert _object_organization_id(obj) is None


def test_association_with_different_tenants_is_rejected():
    obj = _workflow_object("risks.riskasset", risk=_tenant_root(73), asset=_tenant_root(91))
    assert _object_organization_id(obj) is None


def test_association_with_missing_tenant_side_is_rejected():
    obj = _workflow_object("risks.riskasset", risk=_tenant_root(73), asset=None)
    assert _object_organization_id(obj) is None
