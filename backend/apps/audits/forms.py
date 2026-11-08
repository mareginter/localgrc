from django import forms

from .models import Audit, AuditFinding, CorrectiveAction


class AuditForm(forms.ModelForm):
    class Meta:
        model = Audit
        fields = [
            "title", "scope", "audit_type", "auditor_org", "lead_auditor",
            "planned_start", "planned_end", "actual_start", "actual_end", "status",
        ]
        widgets = {
            "scope": forms.Textarea(attrs={"rows": 3}),
            "planned_start": forms.DateInput(attrs={"type": "date"}),
            "planned_end": forms.DateInput(attrs={"type": "date"}),
            "actual_start": forms.DateInput(attrs={"type": "date"}),
            "actual_end": forms.DateInput(attrs={"type": "date"}),
        }


class AuditFindingForm(forms.ModelForm):
    class Meta:
        model = AuditFinding
        fields = ["severity", "title", "description", "requirement", "control", "status"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class CorrectiveActionForm(forms.ModelForm):
    class Meta:
        model = CorrectiveAction
        fields = ["description", "responsible", "due_date", "status"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }