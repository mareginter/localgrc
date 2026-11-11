from apps.core.tenant_forms import TenantScopedModelFormMixin
from django import forms
from .models import Vulnerability

class VulnerabilityForm(TenantScopedModelFormMixin, forms.ModelForm):
    class Meta:
        model = Vulnerability
        fields = ['title', 'cve_id', 'description', 'affected_endpoint', 'cvss_score', 'severity', 'status', 'remediation_plan', 'due_date', 'owner']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'remediation_plan': forms.Textarea(attrs={'rows': 3}),
        }
