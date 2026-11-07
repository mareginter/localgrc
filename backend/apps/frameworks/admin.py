from django.contrib import admin

from .models import Framework, FrameworkVersion, Requirement


class FrameworkVersionInline(admin.TabularInline):
    model = FrameworkVersion
    extra = 0
    fields = ("version", "published_at", "is_active")


@admin.register(Framework)
class FrameworkAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "category", "organization", "is_system")
    list_filter = ("category", "organization", "is_system")
    search_fields = ("name", "code")
    inlines = [FrameworkVersionInline]


@admin.register(FrameworkVersion)
class FrameworkVersionAdmin(admin.ModelAdmin):
    list_display = ("framework", "version", "is_active", "published_at")
    list_filter = ("is_active", "framework")
    search_fields = ("framework__name", "version")


@admin.register(Requirement)
class RequirementAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "framework_version", "category", "parent")
    list_filter = ("framework_version", "category")
    search_fields = ("code", "title", "description")
    ordering = ("framework_version", "order", "code")