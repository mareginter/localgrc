from django.db import models
from django.utils import timezone as dj_timezone

from apps.core.mixins import BaseModel


class Audit(BaseModel):
    TYPE_CHOICES = [
        ("internal", "Internal"),
        ("external", "External"),
        ("certification", "Certification"),
        ("supplier", "Supplier"),
    ]
    STATUS_CHOICES = [
        ("planned", "Planned"),
        ("in_progress", "In progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    organization = models.ForeignKey(
        "core.Organization", on_delete=models.CASCADE, related_name="audits"
    )
    code = models.CharField(max_length=32, blank=True, db_index=True)
    title = models.CharField(max_length=255)
    scope = models.TextField(blank=True)
    audit_type = models.CharField(max_length=16, choices=TYPE_CHOICES, default="internal")
    auditor_org = models.CharField(max_length=255, blank=True)
    lead_auditor = models.ForeignKey(
        "core.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="led_audits"
    )
    planned_start = models.DateField(null=True, blank=True)
    planned_end = models.DateField(null=True, blank=True)
    actual_start = models.DateField(null=True, blank=True)
    actual_end = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="planned")
    custom_fields = models.JSONField(default=dict, blank=True)

    class Meta(BaseModel.Meta):
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "audit_type"]),
        ]

    def __str__(self):
        return f"{self.code} - {self.title}" if self.code else self.title

    def save(self, *args, **kwargs):
        if not self.code and self.organization_id:
            existing = Audit.all_objects.filter(
                organization_id=self.organization_id, code__startswith="AUD-"
            ).values_list("code", flat=True)
            nums = []
            for c in existing:
                try:
                    nums.append(int(c.split("-")[1]))
                except (ValueError, IndexError):
                    pass
            self.code = f"AUD-{(max(nums) if nums else 0) + 1:04d}"
        super().save(*args, **kwargs)


class AuditFinding(BaseModel):
    SEVERITY_CHOICES = [
        ("observation", "Observation"),
        ("minor_nc", "Minor non-conformity"),
        ("major_nc", "Major non-conformity"),
        ("opportunity", "Opportunity for improvement"),
    ]
    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In progress"),
        ("resolved", "Resolved"),
        ("verified", "Verified"),
        ("closed", "Closed"),
    ]

    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name="findings")
    code = models.CharField(max_length=32, blank=True, db_index=True)
    severity = models.CharField(max_length=16, choices=SEVERITY_CHOICES, default="observation")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    requirement = models.ForeignKey(
        "frameworks.Requirement", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="audit_findings"
    )
    control = models.ForeignKey(
        "controls.Control", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="audit_findings"
    )
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="open")

    class Meta(BaseModel.Meta):
        indexes = [
            models.Index(fields=["audit", "severity"]),
            models.Index(fields=["audit", "status"]),
        ]

    def __str__(self):
        return f"{self.code} - {self.title}" if self.code else self.title

    def save(self, *args, **kwargs):
        if not self.code and self.audit_id:
            org_id = self.audit.organization_id
            existing = AuditFinding.all_objects.filter(
                audit__organization_id=org_id, code__startswith="FND-"
            ).values_list("code", flat=True)
            nums = []
            for c in existing:
                try:
                    nums.append(int(c.split("-")[1]))
                except (ValueError, IndexError):
                    pass
            self.code = f"FND-{(max(nums) if nums else 0) + 1:04d}"
        super().save(*args, **kwargs)


class CorrectiveAction(BaseModel):
    STATUS_CHOICES = [
        ("planned", "Planned"),
        ("in_progress", "In progress"),
        ("completed", "Completed"),
        ("verified", "Verified"),
        ("cancelled", "Cancelled"),
    ]

    finding = models.ForeignKey(
        AuditFinding, on_delete=models.CASCADE, related_name="corrective_actions"
    )
    description = models.TextField(blank=True)
    responsible = models.ForeignKey(
        "core.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="planned")
    completed_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        "core.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)

    class Meta(BaseModel.Meta):
        indexes = [models.Index(fields=["finding", "status"])]

    def __str__(self):
        return f"{self.finding.code} - CA {self.pk.hex[:6] if self.pk else 'new'}"

    def save(self, *args, **kwargs):
        if self.status == "completed" and not self.completed_at:
            self.completed_at = dj_timezone.now()
        super().save(*args, **kwargs)