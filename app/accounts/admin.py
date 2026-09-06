from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Organization, User


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["name"]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        *BaseUserAdmin.fieldsets,
        ("Organization", {"fields": ("organization",)}),
    )
    add_fieldsets = (
        *BaseUserAdmin.add_fieldsets,
        ("Organization", {"fields": ("organization",)}),
    )
    list_display = (*BaseUserAdmin.list_display, "organization")
    list_filter = (*BaseUserAdmin.list_filter, "organization")
    list_select_related = ["organization"]
