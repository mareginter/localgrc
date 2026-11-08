from django.contrib import admin

from .models import Vendor, VendorAssessment, VendorControl, VendorRisk


class VendorAssessmentInline(admin.TabularInline):
    model = VendorAssessment
    extra = 0
    fields = ("assessment_date", "score", "risk_rating", "next_assessment_date", "assessed_by")


class VendorRiskInline(admin.TabularInline):
    model = VendorRisk
    extra = 0
    autocomplete_fields = ("risk",)


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "criticality", "data_processing_role", "dpa_signed", "status", "organization")
    list_filter = ("criticality", "status", "data_processing_role", "dpa_signed", "organization")
    search_fields = ("name", "description", "contact_email")
    inlines = [VendorAssessmentInline, VendorRiskInline]


@admin.register(VendorAssessment)
class VendorAssessmentAdmin(admin.ModelAdmin):
    list_display = ("vendor", "assessment_date", "score", "risk_rating", "next_assessment_date")
    list_filter = ("risk_rating",)
    search_fields = ("vendor__name",)


@admin.register(VendorRisk)
class VendorRiskAdmin(admin.ModelAdmin):
    list_display = ("vendor", "risk")
    search_fields = ("vendor__name", "risk__code")


@admin.register(VendorControl)
class VendorControlAdmin(admin.ModelAdmin):
    list_display = ("vendor", "control", "verified", "verified_at")
    list_filter = ("verified",)
    search_fields = ("vendor__name", "control__code")