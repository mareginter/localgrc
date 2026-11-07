from django.contrib import admin

from .models import Control, ControlImplementation, ControlRequirement


class ControlRequirementInline(admin.TabularInline):
    model = ControlRequirement
    extra = 0
    fields = ("requirement", "coverage", "justification")
    autocomplete_fields = ("requirement",)


class ControlImplementationInline(admin.TabularInline):
    model = ControlImplementation
    extra = 0
    fields = ("department", "status", "last_tested_at", "next_test_at")


@admin.register(Control)
class ControlAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "control_type", "status", "category", "organization", "owner")
    list_filter = ("control_type", "status", "category", "organization")
    search_fields = ("code", "name", "description")
    readonly_fields = ("code",)
    inlines = [ControlRequirementInline, ControlImplementationInline]


@admin.register(ControlRequirement)
class ControlRequirementAdmin(admin.ModelAdmin):
    list_display = ("control", "requirement", "coverage")
    list_filter = ("coverage",)
    search_fields = ("control__code", "requirement__code")


@admin.register(ControlImplementation)
class ControlImplementationAdmin(admin.ModelAdmin):
    list_display = ("control", "department", "status", "last_tested_at", "next_test_at")
    list_filter = ("status", "department")
    search_fields = ("control__code",)