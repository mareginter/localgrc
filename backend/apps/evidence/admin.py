from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from .models import Evidence


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ("title", "content_type", "object_id", "source", "valid_until", "verified_at", "organization")
    list_filter = ("source", "content_type", "organization")
    search_fields = ("title", "description")
    readonly_fields = ("content_type", "object_id")
    date_hierarchy = "collected_at"