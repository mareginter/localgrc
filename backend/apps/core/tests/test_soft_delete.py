from apps.core.models import Organization


def test_soft_delete_hides_from_default_manager(db):
    org = Organization.objects.create(name="A", slug="a")
    assert Organization.objects.count() == 1
    org.soft_delete()
    assert Organization.objects.count() == 0
    assert Organization.all_objects.count() == 1


def test_restore(db):
    org = Organization.objects.create(name="A", slug="a")
    org.soft_delete()
    org.restore()
    assert Organization.objects.filter(pk=org.pk).exists()
