from django.contrib import admin

from .models import Policy, PolicyApproval, PolicyVersion


class PolicyVersionInline(admin.TabularInline):
    model = PolicyVersion
    extra = 0
    fields = ("version_number", "effective_date", "review_date", "next_review_date", "approved_by")
    readonly_fields = ("version_number",)


class PolicyApprovalInline(admin.TabularInline):
    model = PolicyApproval
    extra = 0
    fields = ("approver", "decision", "comment", "decided_at")
    readonly_fields = ("decided_at",)


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "category", "status", "organization", "owner")
    list_filter = ("status", "category", "organization")
    search_fields = ("code", "title", "summary")
    readonly_fields = ("code",)
    inlines = [PolicyVersionInline]


@admin.register(PolicyVersion)
class PolicyVersionAdmin(admin.ModelAdmin):
    list_display = ("policy", "version_number", "effective_date", "next_review_date")
    list_filter = ("policy",)
    search_fields = ("policy__code", "policy__title")
    inlines = [PolicyApprovalInline]


@admin.register(PolicyApproval)
class PolicyApprovalAdmin(admin.ModelAdmin):
    list_display = ("policy_version", "approver", "decision", "decided_at")
    list_filter = ("decision",)
    search_fields = ("policy_version__policy__code",)