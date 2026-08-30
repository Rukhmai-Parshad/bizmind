from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from accounts.models import User
from .forms import DatasetUploadForm


class DatasetUploadFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="analyst@example.com",
            password="strong-password-123",
        )

    def test_rejects_non_csv_files(self):
        upload = SimpleUploadedFile("data.txt", b"hello")
        form = DatasetUploadForm(
            data={"name": "Test", "type": "sales"},
            files={"file": upload},
            user=self.user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Only CSV files are supported.", form.errors["file"])
