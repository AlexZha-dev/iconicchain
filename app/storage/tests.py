from tempfile import TemporaryDirectory

from accounts.models import Organization, User
from django.test import override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Download, StoredFile


class StorageApiTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.media_directory = TemporaryDirectory()
        cls.media_settings = override_settings(MEDIA_ROOT=cls.media_directory.name)
        cls.media_settings.enable()

    @classmethod
    def tearDownClass(cls):
        cls.media_settings.disable()
        cls.media_directory.cleanup()
        super().tearDownClass()

    def setUp(self):
        self.organization = Organization.objects.create(name="Acme")
        self.user = User.objects.create_user(
            username="alice",
            password="safe-test-password",
            organization=self.organization,
        )
        self.client.force_authenticate(self.user)
        self.file_list_url = reverse("storage:file-list")

    def upload(self, name="report.txt", content=b"hello"):
        return self.client.post(
            self.file_list_url,
            {"file": SimpleUploadedFile(name, content)},
            format="multipart",
        )

    def test_file_list_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.file_list_url)

        self.assertIn(
            response.status_code,
            {status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN},
        )

    def test_upload_uses_the_authenticated_users_organization(self):
        response = self.upload()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        stored_file = StoredFile.objects.get()
        self.assertEqual(stored_file.organization, self.organization)
        self.assertEqual(stored_file.uploaded_by, self.user)
        self.assertEqual(stored_file.original_name, "report.txt")
        self.assertEqual(stored_file.size, 5)
        self.assertTrue(
            stored_file.file.name.startswith(f"organizations/{self.organization.pk}/")
        )
        self.assertEqual(response.data["download_count"], 0)

    @override_settings(DATA_UPLOAD_MAX_NUMBER_FILES=2)
    def test_upload_rejects_more_than_one_file(self):
        response = self.client.post(
            self.file_list_url,
            {
                "file": [
                    SimpleUploadedFile("one.txt", b"one"),
                    SimpleUploadedFile("two.txt", b"two"),
                ]
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(StoredFile.objects.count(), 0)

    def test_get_records_download_but_head_does_not(self):
        self.upload(name="notes.txt", content=b"notes")
        stored_file = StoredFile.objects.get()
        download_url = reverse("storage:file-download", args=[stored_file.pk])

        response = self.client.get(download_url)

        try:
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(b"".join(response.streaming_content), b"notes")
            self.assertTrue(response["Content-Disposition"].startswith("attachment;"))
            self.assertEqual(
                Download.objects.filter(file=stored_file, user=self.user).count(), 1
            )
        finally:
            response.close()

        head_response = self.client.head(download_url)

        try:
            self.assertEqual(head_response.status_code, status.HTTP_200_OK)
            self.assertEqual(
                Download.objects.filter(file=stored_file, user=self.user).count(), 1
            )
        finally:
            head_response.close()
