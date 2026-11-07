from django import forms

from .models import Asset, Risk, RiskAssessment, RiskTreatment


class RiskForm(forms.ModelForm):
    class Meta:
        model = Risk
        fields = ["title", "description", "category", "department", "owner", "status"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ["name", "type", "owner", "criticality", "classification", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class AssessmentForm(forms.ModelForm):
    class Meta:
        model = RiskAssessment
        fields = ["type", "likelihood", "impact", "rationale", "is_current"]
        widgets = {"rationale": forms.Textarea(attrs={"rows": 3})}


class TreatmentForm(forms.ModelForm):
    class Meta:
        model = RiskTreatment
        fields = ["strategy", "description", "responsible", "due_date", "status"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }