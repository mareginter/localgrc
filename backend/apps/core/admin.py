from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (
    Attachment, AuditLog, Comment, Notification, NotificationPreference,
    Organization, Role, Tag, TaggedItem, User, UserRole,
    WorkflowDefinition, WorkflowInstance, WorkflowState, WorkflowTransition,
)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "is_active", "is_staff")
    search_fields = ("email", "first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal", {"fields": ("first_name", "last_name", "locale", "timezone")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "slug")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_system")


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "organization", "created_at")
    list_filter = ("role", "organization")
    search_fields = ("user__email",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "entity_type", "entity_id", "actor")
    list_filter = ("action", "entity_type")
    readonly_fields = tuple(f.name for f in AuditLog._meta.fields)
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


admin.site.register(Tag)
admin.site.register(TaggedItem)
admin.site.register(Comment)
admin.site.register(Attachment)
admin.site.register(Notification)
admin.site.register(NotificationPreference)
admin.site.register(WorkflowDefinition)
admin.site.register(WorkflowState)
admin.site.register(WorkflowTransition)
admin.site.register(WorkflowInstance)
