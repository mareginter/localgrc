from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone as dj_timezone

from apps.core.mixins import BaseModel


class Asset(BaseModel):
    TYPE_CHOICES = [
        ("data", "Data"), ("system", "System"), ("service", "Service"),
        ("people", "People"), ("facility", "Facility"), ("third_party", "Third party"),
    ]
    CRITICALITY_CHOICES = [
        ("low", "Low"), ("medium", "Medium"), ("high", "High"), ("critical", "Critical"),
    ]
    CLASSIFICATION_CHOICES = [
        ("public", "Public"), ("internal", "Internal"),
        ("confidential", "Confidential"), ("restricted", "Restricted"),
    ]

    organization = models.ForeignKey("core.Organization", on_delete=models.CASCADE, related_name="assets")
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=32, choices=TYPE_CHOICES, default="system")
    owner = models.ForeignKey("core.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="owned_assets")
    criticality = models.CharField(max_length=16, choices=CRITICALITY_CHOICES, default="medium")
    classification = models.CharField(max_length=16, choices=CLASSIFICATION_CHOICES, default="internal")
    description = models.TextField(blank=True)

    class Meta(BaseModel.Meta):
        indexes = [models.Index(fields=["organization", "criticality"])]

    def __str__(self):
        return self.name


class Risk(BaseModel):
    CATEGORY_CHOICES = [
        ("operational", "Operational"), ("security", "Security"), ("privacy", "Privacy"),
        ("compliance", "Compliance"), ("strategic", "Strategic"), ("financial", "Financial"),
    ]
    STATUS_CHOICES = [
        ("draft", "Draft"), ("under_review", "Under review"), ("approved", "Approved"),
        ("rejected", "Rejected"), ("mitigating", "Mitigating"), ("closed", "Closed"),
    ]

    organization = models.ForeignKey("core.Organization", on_delete=models.CASCADE, related_name="risks")
    code = models.CharField(max_length=32, blank=True, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default="operational")
    department = models.CharField(max_length=100, blank=True, db_index=True)
    owner = models.ForeignKey("core.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="owned_risks")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="draft")
    custom_fields = models.JSONField(default=dict, blank=True)

    class Meta(BaseModel.Meta):
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "category"]),
        ]

    def __str__(self):
        return f"{self.code} â€” {self.title}" if self.code else self.title

    def save(self, *args, **kwargs):
        if not self.code and self.organization_id:
            existing = Risk.all_objects.filter(
                organization_id=self.organization_id, code__startswith="R-"
            ).values_list("code", flat=True)
            nums = []
            for c in existing:
                try: nums.append(int(c.split("-")[1]))
                except (ValueError, IndexError): pass
            self.code = f"R-{(max(nums) if nums else 0) + 1:04d}"
        super().save(*args, **kwargs)

    def current_assessment(self, assessment_type="residual"):
        return self.assessments.filter(type=assessment_type, is_current=True).first()

    @property
    def inherent_score(self):
        a = self.current_assessment("inherent")
        return a.score if a else None

    @property
    def residual_score(self):
        a = self.current_assessment("residual")
        return a.score if a else None

    @property
    def risk_level(self):
        score = self.residual_score or self.inherent_score
        if score is None: return "unknown"
        if score >= 20: return "critical"
        if score >= 12: return "high"
        if score >= 6: return "medium"
        return "low"


class RiskAssessment(BaseModel):
    TYPE_CHOICES = [("inherent", "Inherent"), ("residual", "Residual"), ("target", "Target")]

    risk = models.ForeignKey(Risk, on_delete=models.CASCADE, related_name="assessments")
    type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    likelihood = models.PositiveSmallIntegerField()
    impact = models.PositiveSmallIntegerField()
    rationale = models.TextField(blank=True)
    assessed_by = models.ForeignKey("core.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    assessed_at = models.DateTimeField(default=dj_timezone.now)
    is_current = models.BooleanField(default=True)

    class Meta(BaseModel.Meta):
        indexes = [models.Index(fields=["risk", "type", "is_current"])]

    @property
    def score(self):
        return self.likelihood * self.impact

    def clean(self):
        if not (1 <= self.likelihood <= 5):
            raise ValidationError({"likelihood": "Must be between 1 and 5."})
        if not (1 <= self.impact <= 5):
            raise ValidationError({"impact": "Must be between 1 and 5."})

    def save(self, *args, **kwargs):
        if self.is_current and self.risk_id:
            RiskAssessment.objects.filter(
                risk_id=self.risk_id, type=self.type, is_current=True
            ).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class RiskTreatment(BaseModel):
    STRATEGY_CHOICES = [
        ("mitigate", "Mitigate"), ("accept", "Accept"),
        ("avoid", "Avoid"), ("transfer", "Transfer"),
    ]
    STATUS_CHOICES = [
        ("planned", "Planned"), ("in_progress", "In progress"),
        ("completed", "Completed"), ("cancelled", "Cancelled"),
    ]

    risk = models.ForeignKey(Risk, on_delete=models.CASCADE, related_name="treatments")
    strategy = models.CharField(max_length=16, choices=STRATEGY_CHOICES, default="mitigate")
    description = models.TextField(blank=True)
    responsible = models.ForeignKey("core.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="planned")
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta(BaseModel.Meta):
        indexes = [models.Index(fields=["risk", "status"])]

    def __str__(self):
        return f"{self.get_strategy_display()} â€” {self.risk.code}"


class RiskAsset(BaseModel):
    risk = models.ForeignKey(Risk, on_delete=models.CASCADE, related_name="asset_links")
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="risk_links")

    class Meta(BaseModel.Meta):
        pass
class RiskControl(BaseModel):
    EFFECTIVENESS_CHOICES = [
        ("unknown", "Unknown"),
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    risk = models.ForeignKey(Risk, on_delete=models.CASCADE, related_name="control_links")
    control = models.ForeignKey(
        "controls.Control", on_delete=models.CASCADE, related_name="risk_links"
    )
    effectiveness = models.CharField(max_length=16, choices=EFFECTIVENESS_CHOICES, default="unknown")

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=["risk", "control"], name="uniq_risk_control")
        ]

    def __str__(self):
        return f"{self.risk.code} <- {self.control.code} ({self.effectiveness})"