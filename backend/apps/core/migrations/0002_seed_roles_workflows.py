from django.db import migrations

ROLES = [
    ("admin", "Administrator"),
    ("risk_manager", "Risk Manager"),
    ("auditor", "Auditor"),
    ("control_owner", "Control Owner"),
    ("contributor", "Contributor"),
    ("reader", "Reader"),
]


def seed(apps, schema_editor):
    Role = apps.get_model("core", "Role")
    for code, name in ROLES:
        Role.objects.get_or_create(code=code, defaults={"name": name, "is_system": True})


def unseed(apps, schema_editor):
    Role = apps.get_model("core", "Role")
    Role.objects.filter(code__in=[c for c, _ in ROLES]).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
