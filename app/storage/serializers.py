import unicodedata

from accounts.models import Organization, User
from django.conf import settings
from rest_framework import serializers

from .models import Download, StoredFile
from .services import save_upload


class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


class OrganizationSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["id", "name"]


class OrganizationSerializer(OrganizationSummarySerializer):
    download_count = serializers.IntegerField(read_only=True)

    class Meta(OrganizationSummarySerializer.Meta):
        fields = ["id", "name", "download_count"]


class FileSummarySerializer(serializers.ModelSerializer):
    download_url = serializers.HyperlinkedIdentityField(
        view_name="storage:file-download"
    )

    class Meta:
        model = StoredFile
        fields = ["id", "original_name", "download_url"]


class StoredFileSerializer(FileSummarySerializer):
    organization = OrganizationSummarySerializer(read_only=True)
    uploaded_by = UserSummarySerializer(read_only=True)
    download_count = serializers.IntegerField(read_only=True)

    class Meta(FileSummarySerializer.Meta):
        fields = [
            "id",
            "original_name",
            "size",
            "uploaded_at",
            "organization",
            "uploaded_by",
            "download_count",
            "download_url",
        ]


class StoredFileUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True, allow_empty_file=True, max_length=255)

    class Meta:
        model = StoredFile
        fields = ["file"]

    def to_internal_value(self, data):
        unknown_fields = set(data) - {"file", "csrfmiddlewaretoken"}
        if unknown_fields:
            raise serializers.ValidationError(
                {
                    field: ["Unknown field. Only file may be supplied."]
                    for field in unknown_fields
                }
            )
        return super().to_internal_value(data)

    def validate_file(self, uploaded_file):
        if uploaded_file.size > settings.MAX_UPLOAD_SIZE:
            raise serializers.ValidationError(
                f"File exceeds the {settings.MAX_UPLOAD_SIZE}-byte upload limit."
            )
        name = uploaded_file.name.replace("\\", "/").rsplit("/", 1)[-1]
        if name in {"", ".", ".."} or any(
            unicodedata.category(char).startswith("C") for char in name
        ):
            raise serializers.ValidationError(
                "Use a filename without control characters."
            )
        uploaded_file.name = name
        return uploaded_file

    def create(self, validated_data):
        return save_upload(**validated_data)


class UserDownloadSerializer(serializers.ModelSerializer):
    file = FileSummarySerializer(read_only=True)

    class Meta:
        model = Download
        fields = ["id", "file", "downloaded_at"]


class FileDownloadSerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)

    class Meta:
        model = Download
        fields = ["id", "user", "downloaded_at"]
