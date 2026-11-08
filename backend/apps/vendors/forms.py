from django import forms

from .models import Vendor, VendorAssessment, VendorControl, VendorRisk


class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = [
            "name", "description", "category", "criticality",
            "data_processing_role", "dpa_signed", "dpa_date",
            "contact_name", "contact_email", "contact_phone", "status",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "dpa_date": forms.DateInput(attrs={"type": "date"}),
        }


class VendorAssessmentForm(forms.ModelForm):
    class Meta:
        model = VendorAssessment
        fields = ["assessment_date", "score", "risk_rating", "findings_summary", "next_assessment_date"]
        widgets = {
            "assessment_date": forms.DateInput(attrs={"type": "date"}),
            "next_assessment_date": forms.DateInput(attrs={"type": "date"}),
            "findings_summary": forms.Textarea(attrs={"rows": 3}),
        }


class VendorRiskForm(forms.ModelForm):
    class Meta:
        model = VendorRisk
        fields = ["risk", "note"]
        widgets = {"note": forms.Textarea(attrs={"rows": 2})}


class VendorControlForm(forms.ModelForm):
    class Meta:
        model = VendorControl
        fields = ["control", "verified", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 2})}