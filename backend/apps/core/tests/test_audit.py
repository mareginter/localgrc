from apps.core.models import AuditLog, Organization


def test_audit_on_create(db):
    org = Organization.objects.create(name="A", slug="a")
    log = AuditLog.objects.filter(entity_type="core.organization",
                                  entity_id=org.pk, action="create").first()
    assert log is not None and log.after["name"] == "A"


def test_audit_diff_on_update(db):
    org = Organization.objects.create(name="A", slug="a")
    org.name = "B"
    org.save()
    log = AuditLog.objects.filter(entity_type="core.organization",
                                  entity_id=org.pk, action="update").first()
    assert log is not None
    assert log.diff == {"name": {"before": "A", "after": "B"}}


def test_no_audit_when_nothing_changed(db):
    org = Organization.objects.create(name="A", slug="a")
    before = AuditLog.objects.count()
    org.save()
    assert AuditLog.objects.count() == before


def test_audit_log_resolves_organization_through_child_relations(org):
    from apps.audits.models import Audit, AuditFinding, CorrectiveAction
    from apps.controls.models import Control, ControlImplementation
    from apps.frameworks.models import Framework, FrameworkVersion, Requirement

    audit = Audit.objects.create(
        organization=org, title="Internal audit", status="planned"
    )
    finding = AuditFinding.objects.create(
        audit=audit, title="Missing evidence", status="open"
    )
    action = CorrectiveAction.objects.create(
        finding=finding, description="Collect evidence"
    )

    control = Control.objects.create(organization=org, name="Access control")
    implementation = ControlImplementation.objects.create(control=control)

    framework = Framework.objects.create(
        organization=org, code="TEST", name="Test framework"
    )
    version = FrameworkVersion.objects.create(framework=framework, version="1.0")
    requirement = Requirement.objects.create(
        framework_version=version, code="REQ-1", title="Test requirement"
    )

    expected = {
        ("audits.auditfinding", finding.pk),
        ("audits.correctiveaction", action.pk),
        ("controls.controlimplementation", implementation.pk),
        ("frameworks.frameworkversion", version.pk),
        ("frameworks.requirement", requirement.pk),
    }
    actual = set(
        AuditLog.objects.filter(
            organization=org,
            entity_type__in=[item[0] for item in expected],
            entity_id__in=[item[1] for item in expected],
        ).values_list("entity_type", "entity_id")
    )
    assert actual == expected
