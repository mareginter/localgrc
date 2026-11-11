from apps.core.tenant_forms import TenantScopedModelFormMixin
from django import forms

from .models import Policy, PolicyApproval, PolicyVersion


class PolicyForm(TenantScopedModelFormMixin, forms.ModelForm):
    class Meta:
        model = Policy
        fields = ["title", "summary", "category", "owner", "status"]
        widgets = {"summary": forms.Textarea(attrs={"rows": 3})}


class PolicyVersionForm(TenantScopedModelFormMixin, forms.ModelForm):
    class Meta:
        model = PolicyVersion
        fields = [
            "content", "file_attachment",
            "effective_date", "review_date", "next_review_date", "change_summary",
        ]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 12}),
            "change_summary": forms.Textarea(attrs={"rows": 2}),
            "effective_date": forms.DateInput(attrs={"type": "date"}),
            "review_date": forms.DateInput(attrs={"type": "date"}),
            "next_review_date": forms.DateInput(attrs={"type": "date"}),
        }


class PolicyApprovalForm(TenantScopedModelFormMixin, forms.ModelForm):
    class Meta:
        model = PolicyApproval
        fields = ["decision", "comment"]
        widgets = {"comment": forms.Textarea(attrs={"rows": 2})}