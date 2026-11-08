from datetime import timedelta

from django.db import models
from django.utils import timezone as dj_timezone

from apps.core.mixins import BaseModel


# Offsets for regulatory deadlines (from detected_at)
REGULATION_OFFSETS = {
    "gdpr_72h": timedelta(hours=72),
    "nis2_24h": timedelta(hours=24),
    "nis2_72h": timedelta(hours=72),
    "nis2_1m": timedelta(days=30),
}


class Incident(BaseModel):
    CATEGORY_CHOICES = [
        ("security", "Security incident"),
        ("data_breach", "Data breach"),
        ("service_disruption", "Service disruption"),
        ("fraud", "Fraud"),
        ("physical", "Physical security"),
        ("other", "Other"),
    ]
    SEVERITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]
    STATUS_CHOICES = [
        ("detected", "Detected"),
        ("triaged", "Triaged"),
        ("contained", "Contained"),
        ("eradicated", "Eradicated"),
        ("recovered", "Recovered"),
        ("closed", "Closed"),
    ]

    organization = models.ForeignKey(
        "core.Organization", on_delete=models.CASCADE, related_name="incidents"
    )
    code = models.CharField(max_length=32, blank=True, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default="security")
    severity = models.CharField(max_length=16, choices=SEVERITY_CHOICES, default="medium")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="detected")

    detected_at = models.DateTimeField(default=dj_timezone.now)
    occurred_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    reported_by = models.ForeignKey(
        "core.User", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="reported_incidents"
    )
    owner = models.ForeignKey(
        "core.User", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="owned_incidents"
    )
    affected_systems = models.TextField(blank=True)
    custom_fields = models.JSONField(default=dict, blank=True)

    class Meta(BaseModel.Meta):
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "severity"]),
            models.Index(fields=["organization", "category"]),
        ]

    def __str__(self):
        return f"{self.code} - {self.title}" if self.code else self.title

    def save(self, *args, **kwargs):
        if not self.code and self.organization_id:
            existing = Incident.all_objects.filter(
                organization_id=self.organization_id, code__startswith="INC-"
            ).values_list("code", flat=True)
            nums = []
            for c in existing:
                try:
                    nums.append(int(c.split("-")[1]))
                except (ValueError, IndexError):
                    pass
            self.code = f"INC-{(max(nums) if nums else 0) + 1:04d}"
        super().save(*args, **kwargs)

    @property
    def is_high_severity(self):
        return self.severity in ("high", "critical")


class RegulatoryDeadline(BaseModel):
    REGULATION_CHOICES = [
        ("gdpr_72h", "GDPR Art. 33 (72h)"),
        ("nis2_24h", "NIS2 early warning (24h)"),
        ("nis2_72h", "NIS2 notification (72h)"),
        ("nis2_1m", "NIS2 final report (30d)"),
        ("other", "Other"),
    ]

    incident = models.ForeignKey(
        Incident, on_delete=models.CASCADE, related_name="deadlines"
    )
    regulation = models.CharField(max_length=16, choices=REGULATION_CHOICES)
    deadline_at = models.DateTimeField()
    notified_at = models.DateTimeField(null=True, blank=True)
    regulator_reference = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    class Meta(BaseModel.Meta):
        indexes = [
            models.Index(fields=["incident", "regulation"]),
            models.Index(fields=["deadline_at"]),
            models.Index(fields=["notified_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["incident", "regulation"], name="uniq_incident_regulation"
            )
        ]

    def __str__(self):
        return f"{self.incident.code} - {self.get_regulation_display()}"

    @property
    def is_notified(self):
        return self.notified_at is not None

    @property
    def is_overdue(self):
        return not self.is_notified and dj_timezone.now() > self.deadline_at

    @property
    def time_remaining(self):
        if self.is_notified:
            return None
        return self.deadline_at - dj_timezone.now()

    @property
    def status_label(self):
        if self.is_notified:
            return "notified"
        if self.is_overdue:
            return "overdue"
        remaining = self.deadline_at - dj_timezone.now()
        hours = remaining.total_seconds() / 3600
        if hours <= 24:
            return "urgent"
        return "pending"


class IncidentAsset(BaseModel):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="asset_links")
    asset = models.ForeignKey("risks.Asset", on_delete=models.CASCADE, related_name="incident_links")

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=["incident", "asset"], name="uniq_incident_asset")
        ]


class IncidentVendor(BaseModel):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="vendor_links")
    vendor = models.ForeignKey("vendors.Vendor", on_delete=models.CASCADE, related_name="incident_links")
    notes = models.TextField(blank=True)

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=["incident", "vendor"], name="uniq_incident_vendor")
        ]


class IncidentRisk(BaseModel):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="risk_links")
    risk = models.ForeignKey("risks.Risk", on_delete=models.CASCADE, related_name="incident_links")

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=["incident", "risk"], name="uniq_incident_risk")
        ]


def ensure_regulatory_deadlines(incident):
    """Create default deadlines based on incident category. Idempotent."""
    if incident.category == "data_breach":
        RegulatoryDeadline.objects.get_or_create(
            incident=incident, regulation="gdpr_72h",
            defaults={"deadline_at": incident.detected_at + REGULATION_OFFSETS["gdpr_72h"]},
        )