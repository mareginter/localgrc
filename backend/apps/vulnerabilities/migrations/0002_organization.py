from django.db import migrations, models
import django.db.models.deletion

def backfill_single_org(apps, schema_editor):
    Organization = apps.get_model("core", "Organization")
    Vulnerability = apps.get_model("vulnerabilities", "Vulnerability")
    db = schema_editor.connection.alias
    orgs = Organization.objects.using(db).filter(deleted_at__isnull=True)
    if orgs.count() == 1:
        Vulnerability.objects.using(db).filter(organization__isnull=True).update(organization=orgs.first().pk)

class Migration(migrations.Migration):
    dependencies = [('core', '0002_seed_roles_workflows'), ('vulnerabilities', '0001_initial')]
    operations = [migrations.AddField(
        model_name='vulnerability', name='organization',
        field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='vulnerabilities', to='core.organization'),
    ), migrations.RunPython(backfill_single_org, migrations.RunPython.noop)]
