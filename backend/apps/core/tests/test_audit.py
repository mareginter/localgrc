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
