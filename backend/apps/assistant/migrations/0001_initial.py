import uuid
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(name='Document', fields=[
            ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ('title', models.CharField(max_length=255)),
            ('file', models.FileField(upload_to='rag_documents/')),
            ('uploaded_at', models.DateTimeField(auto_now_add=True)),
        ]),
        migrations.CreateModel(name='DocumentChunk', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('text', models.TextField()), ('embedding', models.JSONField()),
            ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chunks', to='assistant.document')),
        ]),
    ]
