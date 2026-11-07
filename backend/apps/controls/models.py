from django.db import models

from apps.core.mixins import BaseModel


class Control(BaseModel):
    TYPE_CHOICES = [
        ("preventive", "Preventive"),
        ("detective", "Detective"),
        ("corrective", "Corrective"),
        ("directive", "Directive"),
    ]
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("approved", "Approved"),
        ("implemented", "Implemented"),
        ("retired", "Retired"),
    ]

    organization = models.ForeignKey(
        "core.Organization", on_delete=models.CASCADE, related_name="controls"
    )
    code = models.CharField(max_length=32, blank=True, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    control_type = models.CharField(max_length=16, choices=TYPE_CHOICES, default="preventive")
    category = models.CharField(max_length=64, blank=True)
    owner = models.ForeignKey(
        "core.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="owned_controls"
    )
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="draft")
    custom_fields = models.JSONField(default=dict, blank=True)

    class Meta(BaseModel.Meta):
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "control_type"]),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}" if self.code else self.name

    def save(self, *args, **kwargs):
        if not self.code and self.organization_id:
            existing = Control.all_objects.filter(
                organization_id=self.organization_id, code__startswith="CTL-"
            ).values_list("code", flat=True)
            nums = []
            for c in existing:
                try:
                    nums.append(int(c.split("-")[1]))
                except (ValueError, IndexError):
                    pass
            self.code = f"CTL-{(max(nums) if nums else 0) + 1:04d}"
        super().save(*args, **kwargs)


class ControlRequirement(BaseModel):
    COVERAGE_CHOICES = [
        ("full", "Full"),
        ("partial", "Partial"),
        ("na", "Not applicable"),
    ]

    control = models.ForeignKey(Control, on_delete=models.CASCADE, related_name="requirement_links")
    requirement = models.ForeignKey(
        "frameworks.Requirement", on_delete=models.CASCADE, related_name="control_links"
    )
    coverage = models.CharField(max_length=16, choices=COVERAGE_CHOICES, default="full")
    justification = models.TextField(blank=True)

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["control", "requirement"], name="uniq_control_requirement"
            )
        ]
        indexes = [models.Index(fields=["requirement", "coverage"])]

    def __str__(self):
        return f"{self.control.code} -> {self.requirement.code} ({self.coverage})"


class ControlImplementation(BaseModel):
    STATUS_CHOICES = [
        ("not_implemented", "Not implemented"),
        ("partial", "Partial"),
        ("implemented", "Implemented"),
        ("na", "Not applicable"),
    ]

    control = models.ForeignKey(Control, on_delete=models.CASCADE, related_name="implementations")
    department = models.CharField(max_length=100, blank=True, default="", db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="not_implemented")
    description = models.TextField(blank=True)
    last_tested_at = models.DateField(null=True, blank=True)
    next_test_at = models.DateField(null=True, blank=True)

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["control", "department"], name="uniq_control_implementation"
            )
        ]
        indexes = [models.Index(fields=["control", "status"])]

    def __str__(self):
        dept = self.department or "Org-wide"
        return f"{self.control.code} @ {dept}"