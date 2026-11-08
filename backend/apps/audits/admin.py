from django.contrib import admin

from .models import Audit, AuditFinding, CorrectiveAction


class AuditFindingInline(admin.TabularInline):
    model = AuditFinding
    extra = 0
    fields = ("code", "severity", "title", "status", "requirement", "control")
    readonly_fields = ("code",)


class CorrectiveActionInline(admin.TabularInline):
    model = CorrectiveAction
    extra = 0
    fields = ("description", "responsible", "due_date", "status", "verified_by", "verified_at")
    readonly_fields = ("completed_at", "verified_at")


@admin.register(Audit)
class AuditAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "audit_type", "status", "planned_start", "planned_end", "lead_auditor")
    list_filter = ("audit_type", "status", "organization")
    search_fields = ("code", "title", "scope")
    readonly_fields = ("code",)
    inlines = [AuditFindingInline]


@admin.register(AuditFinding)
class AuditFindingAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "audit", "severity", "status", "requirement", "control")
    list_filter = ("severity", "status")
    search_fields = ("code", "title", "description")
    readonly_fields = ("code",)
    inlines = [CorrectiveActionInline]


@admin.register(CorrectiveAction)
class CorrectiveActionAdmin(admin.ModelAdmin):
    list_display = ("finding", "status", "responsible", "due_date", "completed_at", "verified_at")
    list_filter = ("status",)
    search_fields = ("finding__code", "description")