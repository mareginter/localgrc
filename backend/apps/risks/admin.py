from django.contrib import admin

from .models import Asset, Risk, RiskAssessment, RiskAsset, RiskTreatment


class RiskAssessmentInline(admin.TabularInline):
    model = RiskAssessment
    extra = 0
    fields = ("type", "likelihood", "impact", "is_current", "assessed_at")
    readonly_fields = ("assessed_at",)


class RiskTreatmentInline(admin.TabularInline):
    model = RiskTreatment
    extra = 0
    fields = ("strategy", "description", "responsible", "due_date", "status")


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "criticality", "classification", "organization", "owner")
    list_filter = ("type", "criticality", "classification")
    search_fields = ("name", "description")


@admin.register(Risk)
class RiskAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "category", "status", "risk_level", "organization", "owner")
    list_filter = ("status", "category", "organization")
    search_fields = ("code", "title", "description")
    readonly_fields = ("code",)
    inlines = [RiskAssessmentInline, RiskTreatmentInline]

    @admin.display(description="Level")
    def risk_level(self, obj):
        return obj.risk_level


@admin.register(RiskAssessment)
class RiskAssessmentAdmin(admin.ModelAdmin):
    list_display = ("risk", "type", "likelihood", "impact", "score", "is_current")
    list_filter = ("type", "is_current")
    search_fields = ("risk__code", "risk__title")


@admin.register(RiskTreatment)
class RiskTreatmentAdmin(admin.ModelAdmin):
    list_display = ("risk", "strategy", "status", "responsible", "due_date")
    list_filter = ("strategy", "status")


admin.site.register(RiskAsset)