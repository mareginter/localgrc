from datetime import timedelta

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone as dj_timezone

from apps.core.mixins import BaseModel


class Evidence(BaseModel):
    SOURCE_CHOICES = [
        ("manual", "Manual upload"),
        ("scan", "Automated scan"),
        ("log_export", "Log export"),
        ("screenshot", "Screenshot"),
        ("attestation", "Attestation"),
        ("other", "Other"),
    ]

    organization = models.ForeignKey(
        "core.Organization", on_delete=models.CASCADE, related_name="evidences"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.UUIDField()
    content_object = GenericForeignKey("content_type", "object_id")

    attachment = models.FileField(upload_to="evidence/%Y/%m/", blank=True)
    source = models.CharField(max_length=16, choices=SOURCE_CHOICES, default="manual")

    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)

    collected_at = models.DateTimeField(default=dj_timezone.now)
    collected_by = models.ForeignKey(
        "core.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    verified_by = models.ForeignKey(
        "core.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)

    class Meta(BaseModel.Meta):
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["organization", "valid_until"]),
            models.Index(fields=["organization", "verified_at"]),
        ]
        verbose_name_plural = "evidence"

    def __str__(self):
        return self.title

    @property
    def is_verified(self):
        return self.verified_at is not None

    @property
    def is_expired(self):
        if not self.valid_until:
            return False
        return self.valid_until < dj_timezone.now().date()

    @property
    def expires_within_days(self):
        if not self.valid_until or self.is_expired:
            return None
        delta = self.valid_until - dj_timezone.now().date()
        return delta.days

    @property
    def is_expiring_soon(self):
        days = self.expires_within_days
        return days is not None and days <= 30

    @property
    def status_label(self):
        if self.is_expired:
            return "expired"
        if self.is_expiring_soon:
            return "expiring"
        if not self.is_verified:
            return "unverified"
        return "valid"

    @property
    def target_type_label(self):
        if self.content_type:
            return self.content_type.model_class()._meta.verbose_name.title() if self.content_type.model_class() else self.content_type.model
        return "-"

    @property
    def target_display(self):
        if self.content_object:
            return str(self.content_object)
        return "(target not found)"