"""Reusable tenant-aware queryset restrictions for ModelForms."""
from django.contrib.auth import get_user_model


class TenantScopedModelFormMixin:
    """Restrict every selectable related object to the active organization."""

    def __init__(self, *args, organization=None, **kwargs):
        self.organization = organization
        super().__init__(*args, **kwargs)
        if organization is None:
            return

        User = get_user_model()
        for name, field in self.fields.items():
            queryset = getattr(field, "queryset", None)
            if queryset is None:
                continue
            model = queryset.model
            if model is User:
                field.queryset = queryset.filter(
                    user_roles__organization=organization,
                    user_roles__deleted_at__isnull=True,
                ).distinct()
                continue
            if any(f.name == "organization" for f in model._meta.get_fields()):
                field.queryset = queryset.filter(organization=organization)
                continue
            if model._meta.label_lower == "frameworks.requirement":
                field.queryset = queryset.filter(
                    framework_version__framework__organization=organization
                )
                continue
            # Unknown related models fail closed rather than exposing cross-tenant choices.
            field.queryset = queryset.none()
