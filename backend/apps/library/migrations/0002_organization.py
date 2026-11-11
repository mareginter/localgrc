from django.db import migrations, models
import django.db.models.deletion

def backfill_single_org(apps, schema_editor):
    Organization = apps.get_model("core", "Organization")
    Model = apps.get_model("library", "DocumentTemplate")
    db = schema_editor.connection.alias
    orgs = Organization.objects.using(db).filter(deleted_at__isnull=True)
    if orgs.count() == 1:
        Model.objects.using(db).filter(organization__isnull=True).update(organization=orgs.first().pk)

class Migration(migrations.Migration):
    dependencies = [("library", "0001_initial"), ("core", "0002_seed_roles_workflows")]
    operations = [
        migrations.AddField(model_name="documenttemplate", name="organization", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="document_templates", to="core.organization")),
        migrations.RunPython(backfill_single_org, migrations.RunPython.noop),
    ]
