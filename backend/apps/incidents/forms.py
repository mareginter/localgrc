from apps.core.tenant_forms import TenantScopedModelFormMixin
from django import forms

from .models import Incident, IncidentAsset, IncidentRisk, IncidentVendor, RegulatoryDeadline


class IncidentForm(TenantScopedModelFormMixin, forms.ModelForm):
    class Meta:
        model = Incident
        fields = [
            "title", "description", "category", "severity", "status",
            "detected_at", "occurred_at", "reported_by", "owner", "affected_systems",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "affected_systems": forms.Textarea(attrs={"rows": 2}),
            "detected_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "occurred_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class RegulatoryDeadlineForm(TenantScopedModelFormMixin, forms.ModelForm):
    regulation = forms.ChoiceField(choices=RegulatoryDeadline.REGULATION_CHOICES)

    class Meta:
        model = RegulatoryDeadline
        fields = ["regulation", "deadline_at", "regulator_reference", "notes"]
        widgets = {
            "deadline_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }


class IncidentRiskForm(TenantScopedModelFormMixin, forms.ModelForm):
    class Meta:
        model = IncidentRisk
        fields = ["risk"]


class IncidentVendorForm(TenantScopedModelFormMixin, forms.ModelForm):
    class Meta:
        model = IncidentVendor
        fields = ["vendor", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 2})}


class IncidentAssetForm(TenantScopedModelFormMixin, forms.ModelForm):
    class Meta:
        model = IncidentAsset
        fields = ["asset"]