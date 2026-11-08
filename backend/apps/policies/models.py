from django.db import models
from django.utils import timezone as dj_timezone

from apps.core.mixins import BaseModel


class Policy(BaseModel):
    CATEGORY_CHOICES = [
        ("governance", "Governance"),
        ("security", "Information Security"),
        ("privacy", "Privacy"),
        ("operational", "Operational"),
        ("hr", "Human Resources"),
        ("it", "IT"),
    ]
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("in_review", "In review"),
        ("approved", "Approved"),
        ("published", "Published"),
        ("retired", "Retired"),
    ]

    organization = models.ForeignKey(
        "core.Organization", on_delete=models.CASCADE, related_name="policies"
    )
    code = models.CharField(max_length=32, blank=True, db_index=True)
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True)
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default="security")
    owner = models.ForeignKey(
        "core.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="owned_policies"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    current_version = models.ForeignKey(
        "policies.PolicyVersion", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+"
    )
    custom_fields = models.JSONField(default=dict, blank=True)

    class Meta(BaseModel.Meta):
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "category"]),
        ]

    def __str__(self):
        return f"{self.code} - {self.title}" if self.code else self.title

    def save(self, *args, **kwargs):
        if not self.code and self.organization_id:
            existing = Policy.all_objects.filter(
                organization_id=self.organization_id, code__startswith="POL-"
            ).values_list("code", flat=True)
            nums = []
            for c in existing:
                try:
                    nums.append(int(c.split("-")[1]))
                except (ValueError, IndexError):
                    pass
            self.code = f"POL-{(max(nums) if nums else 0) + 1:04d}"
        super().save(*args, **kwargs)

    @property
    def latest_version(self):
        return self.versions.order_by("-version_number").first()


class PolicyVersion(BaseModel):
    policy = models.ForeignKey(
        Policy, on_delete=models.CASCADE, related_name="versions"
    )
    version_number = models.PositiveIntegerField()
    content = models.TextField(blank=True)
    file_attachment = models.FileField(upload_to="policies/%Y/%m/", blank=True)
    effective_date = models.DateField(null=True, blank=True)
    review_date = models.DateField(null=True, blank=True)
    next_review_date = models.DateField(null=True, blank=True)
    change_summary = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        "core.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["policy", "version_number"], name="uniq_policy_version"
            )
        ]
        ordering = ("-version_number",)

    def __str__(self):
        return f"{self.policy.code} v{self.version_number}"

    def save(self, *args, **kwargs):
        if not self.version_number and self.policy_id:
            existing = PolicyVersion.all_objects.filter(
                policy_id=self.policy_id
            ).values_list("version_number", flat=True)
            self.version_number = (max(existing) if existing else 0) + 1
        super().save(*args, **kwargs)


class PolicyApproval(BaseModel):
    DECISION_CHOICES = [
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("changes_requested", "Changes requested"),
    ]

    policy_version = models.ForeignKey(
        PolicyVersion, on_delete=models.CASCADE, related_name="approvals"
    )
    approver = models.ForeignKey(
        "core.User", on_delete=models.PROTECT, related_name="policy_approvals"
    )
    decision = models.CharField(max_length=32, choices=DECISION_CHOICES)
    comment = models.TextField(blank=True)
    decided_at = models.DateTimeField(default=dj_timezone.now)

    class Meta(BaseModel.Meta):
        indexes = [models.Index(fields=["policy_version", "-decided_at"])]

    def __str__(self):
        return f"{self.policy_version} -> {self.decision}"