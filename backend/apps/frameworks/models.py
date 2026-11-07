from django.db import models

from apps.core.mixins import BaseModel


class Framework(BaseModel):
    organization = models.ForeignKey(
        "core.Organization", on_delete=models.CASCADE, related_name="frameworks"
    )
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=64, blank=True)
    source_url = models.URLField(blank=True)
    is_system = models.BooleanField(default=False)

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=["organization", "code"], name="uniq_framework_org_code")
        ]

    def __str__(self):
        return self.name


class FrameworkVersion(BaseModel):
    framework = models.ForeignKey(
        Framework, on_delete=models.CASCADE, related_name="versions"
    )
    version = models.CharField(max_length=32)
    published_at = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["framework", "version"], name="uniq_framework_version"
            )
        ]

    def __str__(self):
        return f"{self.framework.code} {self.version}"


class Requirement(BaseModel):
    framework_version = models.ForeignKey(
        FrameworkVersion, on_delete=models.CASCADE, related_name="requirements"
    )
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )
    code = models.CharField(max_length=32)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=128, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta(BaseModel.Meta):
        ordering = ("order", "code")
        indexes = [
            models.Index(fields=["framework_version", "category"]),
            models.Index(fields=["framework_version", "parent"]),
        ]

    def __str__(self):
        return f"{self.code} {self.title}"