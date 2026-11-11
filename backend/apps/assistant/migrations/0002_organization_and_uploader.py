from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

def backfill_single_org(apps, schema_editor):
    Organization = apps.get_model("core", "Organization")
    Document = apps.get_model("assistant", "Document")
    db = schema_editor.connection.alias
    orgs = Organization.objects.using(db).filter(deleted_at__isnull=True)
    if orgs.count() == 1:
        Document.objects.using(db).filter(organization__isnull=True).update(organization=orgs.first().pk)

class Migration(migrations.Migration):
    dependencies = [('assistant', '0001_initial'), ('core', '0002_seed_roles_workflows'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.AddField(model_name='document', name='organization', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assistant_documents', to='core.organization')),
        migrations.AddField(model_name='document', name='uploaded_by', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
        migrations.RunPython(backfill_single_org, migrations.RunPython.noop),
    ]
