from typing import override

from accounts.models import Organization
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from .models import Download, StoredFile
from .serializers import (
    FileDownloadSerializer,
    OrganizationSerializer,
    StoredFileSerializer,
    StoredFileUploadSerializer,
    UserDownloadSerializer,
)


@method_decorator(never_cache, name="dispatch")
class APIRootView(APIView):
    """Shared file storage. All endpoints require a logged-in session."""

    def get(self, request):
        return Response(
            {
                "files": reverse("storage:file-list", request=request),
                "organizations": reverse("storage:organization-list", request=request),
                "my_downloads": reverse(
                    "storage:user-downloads",
                    kwargs={"pk": request.user.pk},
                    request=request,
                ),
                "user_downloads_template": "/api/users/{id}/downloads/",
            }
        )


@method_decorator(never_cache, name="dispatch")
class FileListCreateView(generics.ListCreateAPIView):
    """List every organization's files, or upload one file to your organization."""

    parser_classes = [MultiPartParser, FormParser]
    queryset = (
        StoredFile.objects.select_related("organization", "uploaded_by")
        .annotate(download_count=Count("downloads"))
        .order_by("-uploaded_at", "-pk")
    )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return StoredFileUploadSerializer
        return StoredFileSerializer

    def perform_create(self, serializer):
        uploaded_file = serializer.validated_data["file"]
        serializer.save(
            uploaded_by=self.request.user,
            organization=self.request.user.organization,
            original_name=uploaded_file.name,
            size=uploaded_file.size,
        )

    @override
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if sum(len(files) for _, files in request.FILES.lists()) != 1:
            raise ValidationError({"file": ["Upload exactly one file."]})
        self.perform_create(serializer)
        instance = self.get_queryset().get(pk=serializer.instance.pk)
        data = StoredFileSerializer(
            instance, context=self.get_serializer_context()
        ).data
        return Response(data, status=status.HTTP_201_CREATED)


@method_decorator(never_cache, name="dispatch")
class OrganizationListView(generics.ListAPIView):
    """Counts belong to the file's organization, not the downloader's."""

    serializer_class = OrganizationSerializer
    queryset = Organization.objects.annotate(
        download_count=Count("files__downloads")
    ).order_by("name", "pk")


@method_decorator(never_cache, name="dispatch")
class UserDownloadListView(generics.ListAPIView):
    """History for one user. Readable by every authenticated user (see README)."""

    serializer_class = UserDownloadSerializer

    def get_queryset(self):
        user = get_object_or_404(get_user_model(), pk=self.kwargs["pk"])
        return Download.objects.filter(user=user).select_related("file")


@method_decorator(never_cache, name="dispatch")
class FileDownloadListView(generics.ListAPIView):
    serializer_class = FileDownloadSerializer

    def get_queryset(self):
        stored_file = get_object_or_404(StoredFile, pk=self.kwargs["pk"])
        return Download.objects.filter(file=stored_file).select_related("user")


@method_decorator(never_cache, name="dispatch")
class FileDownloadView(APIView):
    """Stream a private attachment and record each prepared GET response."""

    def get(self, request, pk):
        stored_file = get_object_or_404(StoredFile, pk=pk)
        try:
            handle = stored_file.file.storage.open(stored_file.file.name, "rb")
        except FileNotFoundError as exc:
            raise Http404("File content is unavailable.") from exc
        try:
            response = FileResponse(
                handle,
                as_attachment=True,
                filename=stored_file.original_name,
                content_type="application/octet-stream",
            )
            # Django also routes HEAD to get(). Only GET is a download event.
            if request.method == "GET":
                Download.objects.create(user=request.user, file=stored_file)
        except Exception:
            handle.close()
            raise
        return response
