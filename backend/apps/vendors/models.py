from django.db import models
from django.utils import timezone as dj_timezone

from apps.core.mixins import BaseModel


class Vendor(BaseModel):
    CRITICALITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]
    ROLE_CHOICES = [
        ("processor", "Data processor"),
        ("controller", "Data controller"),
        ("sub_processor", "Sub-processor"),
        ("none", "No personal data"),
    ]
    STATUS_CHOICES = [
        ("active", "Active"),
        ("under_review", "Under review"),
        ("terminated", "Terminated"),
    ]

    organization = models.ForeignKey(
        "core.Organization", on_delete=models.CASCADE, related_name="vendors"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=64, blank=True)
    criticality = models.CharField(max_length=16, choices=CRITICALITY_CHOICES, default="medium")
    data_processing_role = models.CharField(max_length=16, choices=ROLE_CHOICES, default="none")
    dpa_signed = models.BooleanField(default=False)
    dpa_date = models.DateField(null=True, blank=True)
    contact_name = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="active")
    custom_fields = models.JSONField(default=dict, blank=True)

    class Meta(BaseModel.Meta):
        indexes = [
            models.Index(fields=["organization", "criticality"]),
            models.Index(fields=["organization", "status"]),
        ]

    def __str__(self):
        return self.name


class VendorAssessment(BaseModel):
    RISK_RATING_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="assessments")
    assessment_date = models.DateField(default=dj_timezone.now)
    score = models.PositiveSmallIntegerField(null=True, blank=True)
    risk_rating = models.CharField(max_length=16, choices=RISK_RATING_CHOICES, default="medium")
    findings_summary = models.TextField(blank=True)
    responses = models.JSONField(default=dict, blank=True)
    assessed_by = models.ForeignKey(
        "core.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    next_assessment_date = models.DateField(null=True, blank=True)

    class Meta(BaseModel.Meta):
        ordering = ("-assessment_date",)
        indexes = [models.Index(fields=["vendor", "-assessment_date"])]

    def __str__(self):
        return f"{self.vendor.name} @ {self.assessment_date}"


class VendorRisk(BaseModel):
    EFFECTIVENESS_CHOICES = [
        ("unknown", "Unknown"),
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="risk_links")
    risk = models.ForeignKey("risks.Risk", on_delete=models.CASCADE, related_name="vendor_links")
    note = models.TextField(blank=True)

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=["vendor", "risk"], name="uniq_vendor_risk")
        ]

    def __str__(self):
        return f"{self.vendor.name} -> {self.risk.code}"


class VendorControl(BaseModel):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="control_links")
    control = models.ForeignKey(
        "controls.Control", on_delete=models.CASCADE, related_name="vendor_links"
    )
    verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=["vendor", "control"], name="uniq_vendor_control")
        ]

    def __str__(self):
        return f"{self.vendor.name} -> {self.control.code}"