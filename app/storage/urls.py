from django.urls import path

from .views import (
    APIRootView,
    FileDownloadListView,
    FileDownloadView,
    FileListCreateView,
    OrganizationListView,
    UserDownloadListView,
)

app_name = "storage"

urlpatterns = [
    path("", APIRootView.as_view(), name="api-root"),
    path("files/", FileListCreateView.as_view(), name="file-list"),
    path("files/<int:pk>/download/", FileDownloadView.as_view(), name="file-download"),
    path(
        "files/<int:pk>/downloads/",
        FileDownloadListView.as_view(),
        name="file-downloads",
    ),
    path("organizations/", OrganizationListView.as_view(), name="organization-list"),
    path(
        "users/<int:pk>/downloads/",
        UserDownloadListView.as_view(),
        name="user-downloads",
    ),
]
