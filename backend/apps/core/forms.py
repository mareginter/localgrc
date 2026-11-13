from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Organization

User = get_user_model()


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        help_text="Define a temporary password for this user.",
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "is_active"]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        if password:
            candidate = User(
                email=cleaned_data.get("email", ""),
                first_name=cleaned_data.get("first_name", ""),
                last_name=cleaned_data.get("last_name", ""),
            )
            try:
                validate_password(password, user=candidate)
            except ValidationError as error:
                self.add_error("password", error)
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    new_password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        help_text="Leave blank to keep current password.",
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "is_active"]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("new_password")
        if password:
            candidate = User(
                email=cleaned_data.get("email", getattr(self.instance, "email", "")),
                first_name=cleaned_data.get("first_name", getattr(self.instance, "first_name", "")),
                last_name=cleaned_data.get("last_name", getattr(self.instance, "last_name", "")),
            )
            try:
                validate_password(password, user=candidate)
            except ValidationError as error:
                self.add_error("new_password", error)
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get("new_password"):
            user.set_password(self.cleaned_data["new_password"])
        if commit:
            user.save()
        return user

class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = [
            "name", "legal_name", "description",
            "vat_number", "registration_number",
            "address_line1", "address_line2", "city", "postal_code", "country",
            "contact_email", "contact_phone", "website",
            "industry", "employee_count", "annual_revenue_eur",
            "regulatory_context", "dpo_name", "dpo_email",
            "logo_url",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
            "regulatory_context": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "name": "Trading name",
            "legal_name": "Legal name",
        }

    def clean_country(self):
        country = self.cleaned_data.get("country", "").upper()
        if country and len(country) != 2:
            raise forms.ValidationError("Use a 2-letter ISO country code (e.g. PT, ES, FR).")
        return country
