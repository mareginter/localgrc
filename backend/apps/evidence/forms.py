from django import forms
from django.contrib.contenttypes.models import ContentType

from .models import Evidence


TARGET_CHOICES = [
    ("controls.control", "Control"),
    ("risks.risktreatment", "Risk treatment"),
    ("audits.auditfinding", "Audit finding"),
    ("audits.correctiveaction", "Corrective action"),
    ("policies.policyversion", "Policy version"),
    ("vendors.vendor", "Vendor"),
]


class EvidenceForm(forms.ModelForm):
    target_type = forms.ChoiceField(choices=TARGET_CHOICES, label="Linked to (type)")
    target_id = forms.UUIDField(
        label="Linked to (UUID)",
        widget=forms.TextInput(attrs={
            "placeholder": "paste the UUID from the target page URL",
            "style": "width:100%;font-family:monospace;",
        }),
    )

    class Meta:
        model = Evidence
        fields = [
            "title", "description", "attachment", "source",
            "valid_from", "valid_until", "collected_at",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "valid_from": forms.DateInput(attrs={"type": "date"}),
            "valid_until": forms.DateInput(attrs={"type": "date"}),
            "collected_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        initial_target_type = kwargs.pop("initial_target_type", None)
        initial_target_id = kwargs.pop("initial_target_id", None)
        super().__init__(*args, **kwargs)
        if initial_target_type:
            self.fields["target_type"].initial = initial_target_type
        if initial_target_id:
            self.fields["target_id"].initial = initial_target_id
        # Pre-fill on edit
        if self.instance and self.instance.pk and self.instance.content_type_id:
            self.fields["target_type"].initial = (
                f"{self.instance.content_type.app_label}.{self.instance.content_type.model}"
            )
            self.fields["target_id"].initial = self.instance.object_id

    def clean(self):
        cleaned = super().clean()
        target_type = cleaned.get("target_type")
        target_id = cleaned.get("target_id")
        if target_type and target_id:
            app_label, model = target_type.split(".", 1)
            try:
                ct = ContentType.objects.get(app_label=app_label, model=model)
                model_class = ct.model_class()
                if not model_class.objects.filter(pk=target_id).exists():
                    raise forms.ValidationError(
                        f"{target_type} with UUID {target_id} not found."
                    )
                cleaned["_content_type"] = ct
            except ContentType.DoesNotExist:
                raise forms.ValidationError(f"Invalid target type: {target_type}")
        return cleaned