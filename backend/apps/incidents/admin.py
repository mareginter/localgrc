from django.contrib import admin

from .models import (
    Incident, IncidentAsset, IncidentRisk, IncidentVendor, RegulatoryDeadline
)


class RegulatoryDeadlineInline(admin.TabularInline):
    model = RegulatoryDeadline
    extra = 0
    fields = ("regulation", "deadline_at", "notified_at", "regulator_reference")


class IncidentRiskInline(admin.TabularInline):
    model = IncidentRisk
    extra = 0
    autocomplete_fields = ("risk",)


class IncidentVendorInline(admin.TabularInline):
    model = IncidentVendor
    extra = 0


class IncidentAssetInline(admin.TabularInline):
    model = IncidentAsset
    extra = 0


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "category", "severity", "status", "detected_at", "organization")
    list_filter = ("category", "severity", "status", "organization")
    search_fields = ("code", "title", "description")
    readonly_fields = ("code",)
    inlines = [RegulatoryDeadlineInline, IncidentRiskInline, IncidentVendorInline, IncidentAssetInline]


@admin.register(RegulatoryDeadline)
class RegulatoryDeadlineAdmin(admin.ModelAdmin):
    list_display = ("incident", "regulation", "deadline_at", "notified_at")
    list_filter = ("regulation",)
    search_fields = ("incident__code", "incident__title")