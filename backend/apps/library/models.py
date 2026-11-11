import uuid
from django.db import models
from django.conf import settings

class DocumentTemplate(models.Model):
    CATEGORY_CHOICES = [
        ('policy', 'Policy Template'),
        ('risk', 'Risk Assessment Form'),
        ('audit', 'Audit Checklist'),
        ('vendor', 'Vendor Questionnaire'),
        ('incident', 'Incident Response Plan'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey("core.Organization", on_delete=models.CASCADE, related_name="document_templates", null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    file = models.FileField(upload_to='library_templates/')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title