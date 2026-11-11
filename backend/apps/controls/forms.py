from apps.core.tenant_forms import TenantScopedModelFormMixin
from django import forms

from .models import Control, ControlImplementation, ControlRequirement


class ControlForm(TenantScopedModelFormMixin, forms.ModelForm):
    class Meta:
        model = Control
        fields = ["name", "description", "control_type", "category", "owner", "status"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}


class ControlRequirementForm(TenantScopedModelFormMixin, forms.ModelForm):
    class Meta:
        model = ControlRequirement
        fields = ["requirement", "coverage", "justification"]
        widgets = {"justification": forms.Textarea(attrs={"rows": 2})}


class ControlImplementationForm(TenantScopedModelFormMixin, forms.ModelForm):
    class Meta:
        model = ControlImplementation
        fields = ["department", "status", "description", "last_tested_at", "next_test_at"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
            "last_tested_at": forms.DateInput(attrs={"type": "date"}),
            "next_test_at": forms.DateInput(attrs={"type": "date"}),
        }