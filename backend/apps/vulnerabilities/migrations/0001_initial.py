import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name='Vulnerability', fields=[
        ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
        ('title', models.CharField(max_length=255)),
        ('cve_id', models.CharField(blank=True, help_text='e.g., CVE-2023-1234', max_length=50)),
        ('description', models.TextField(blank=True)),
        ('affected_endpoint', models.CharField(help_text='e.g., https://api.example.com/login or 192.168.1.50', max_length=255)),
        ('cvss_score', models.DecimalField(blank=True, decimal_places=1, max_digits=3, null=True)),
        ('severity', models.CharField(choices=[('critical', 'Critical (9.0 - 10.0)'), ('high', 'High (7.0 - 8.9)'), ('medium', 'Medium (4.0 - 6.9)'), ('low', 'Low (0.1 - 3.9)'), ('info', 'Informational (0.0)')], default='medium', max_length=20)),
        ('status', models.CharField(choices=[('open', 'Open'), ('in_progress', 'In Progress'), ('mitigated', 'Mitigated'), ('accepted', 'Risk Accepted'), ('false_positive', 'False Positive')], default='open', max_length=20)),
        ('remediation_plan', models.TextField(blank=True)),
        ('discovered_at', models.DateTimeField(auto_now_add=True)),
        ('due_date', models.DateField(blank=True, null=True)),
        ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
    ])]
