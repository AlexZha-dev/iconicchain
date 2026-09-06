from typing import ClassVar
from uuid import uuid4

from django.conf import settings
from django.db import models


def stored_file_path(instance, filename):
    return f"organizations/{instance.organization_id}/{uuid4().hex}"


class StoredFile(models.Model):
    organization = models.ForeignKey(
        "accounts.Organization", on_delete=models.PROTECT, related_name="files"
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_files",
    )
    file = models.FileField(upload_to=stored_file_path, max_length=500)
    original_name = models.CharField(max_length=255)
    size = models.PositiveBigIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at", "-pk"]

    def __str__(self):
        return self.original_name


class Download(models.Model):
    file = models.ForeignKey(
        StoredFile, on_delete=models.PROTECT, related_name="downloads"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="downloads"
    )
    downloaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-downloaded_at", "-pk"]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=["user", "-downloaded_at", "-id"],
                name="dl_user_time_idx",
            ),
            models.Index(
                fields=["file", "-downloaded_at", "-id"],
                name="dl_file_time_idx",
            ),
        ]

    def __str__(self):
        return f"User {self.user_id} downloaded file {self.file_id} at {self.downloaded_at}"
