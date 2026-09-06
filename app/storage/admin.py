from django.contrib import admin

from .models import Download, StoredFile


class ReadOnlyAdmin(admin.ModelAdmin):
    """Keep all file writes and audit events on the authenticated API path."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StoredFile)
class StoredFileAdmin(ReadOnlyAdmin):
    list_display = [
        "id",
        "original_name",
        "organization",
        "uploaded_by",
        "size",
        "uploaded_at",
    ]
    list_filter = ["organization"]
    list_select_related = ["organization", "uploaded_by"]
    search_fields = ["original_name"]
    # Never expose FileField's unprotected .url in the change form.
    fields = [
        "id",
        "original_name",
        "organization",
        "uploaded_by",
        "size",
        "uploaded_at",
    ]
    readonly_fields = fields


@admin.register(Download)
class DownloadAdmin(ReadOnlyAdmin):
    list_display = ["id", "file", "user", "downloaded_at"]
    list_select_related = ["file", "user"]
    fields = ["id", "file", "user", "downloaded_at"]
    readonly_fields = fields
