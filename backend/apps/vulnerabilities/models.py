import uuid
from django.db import models
from django.conf import settings

class Vulnerability(models.Model):
    SEVERITY_CHOICES = [
        ('critical', 'Critical (9.0 - 10.0)'),
        ('high', 'High (7.0 - 8.9)'),
        ('medium', 'Medium (4.0 - 6.9)'),
        ('low', 'Low (0.1 - 3.9)'),
        ('info', 'Informational (0.0)'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('mitigated', 'Mitigated'),
        ('accepted', 'Risk Accepted'),
        ('false_positive', 'False Positive'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    cve_id = models.CharField(max_length=50, blank=True, help_text="e.g., CVE-2023-1234")
    description = models.TextField(blank=True)
    
    affected_endpoint = models.CharField(max_length=255, help_text="e.g., https://api.example.com/login or 192.168.1.50")
    
    cvss_score = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    remediation_plan = models.TextField(blank=True)
    discovered_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.severity.upper()} - {self.title}"

    @property
    def is_overdue(self):
        from django.utils import timezone
        if self.due_date and self.status in ['open', 'in_progress']:
            return self.due_date < timezone.now().date()
        return False
