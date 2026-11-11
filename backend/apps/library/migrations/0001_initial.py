import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name="DocumentTemplate", fields=[
        ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
        ("title", models.CharField(max_length=255)), ("description", models.TextField(blank=True)),
        ("category", models.CharField(choices=[("policy", "Policy Template"), ("risk", "Risk Assessment Form"), ("audit", "Audit Checklist"), ("vendor", "Vendor Questionnaire"), ("incident", "Incident Response Plan"), ("other", "Other")], default="other", max_length=20)),
        ("file", models.FileField(upload_to="library_templates/")), ("uploaded_at", models.DateTimeField(auto_now_add=True)),
        ("uploaded_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
    ])]
