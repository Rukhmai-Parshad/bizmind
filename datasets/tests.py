from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from decisions.models import Decision
from .forms import DatasetUploadForm
from .models import Dataset

PASSWORD = "strong-password-123"

VALID_SALES_CSV = (
    "date,product,region,units_sold,unit_price\n"
    "2024-01-01,Widget,North,2,100\n"
)

MISSING_COLUMN_SALES_CSV = "product,region\nLaptop,North\n"


def csv_upload(name, content):
    return SimpleUploadedFile(name, content.encode("utf-8"), content_type="text/csv")


class DatasetUploadFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="analyst@example.com",
            password=PASSWORD,
            role="ANALYST",
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


class UploadCharacterisationTests(TestCase):
    def setUp(self):
        self.analyst = User.objects.create_user(
            email="analyst@example.com",
            password=PASSWORD,
            role="ANALYST",
        )
        self.viewer = User.objects.create_user(
            email="viewer@example.com",
            password=PASSWORD,
            role="VIEWER",
        )
        self.upload_url = reverse("datasets:upload")

    def test_unauthenticated_upload_redirects_to_login(self):
        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_viewer_is_redirected_and_nothing_is_saved(self):
        self.client.force_login(self.viewer)
        response = self.client.post(
            self.upload_url,
            {
                "name": "Q1 Sales",
                "type": "sales",
                "file": csv_upload("sales.csv", VALID_SALES_CSV),
            },
        )
        self.assertRedirects(response, reverse("dashboard:home"))
        self.assertEqual(Dataset.objects.count(), 0)

    def test_analyst_can_upload_valid_sales_csv(self):
        self.client.force_login(self.analyst)
        response = self.client.post(
            self.upload_url,
            {
                "name": "Q1 Sales",
                "type": "sales",
                "file": csv_upload("sales.csv", VALID_SALES_CSV),
            },
        )
        self.assertRedirects(response, reverse("datasets:dataset_list"))
        dataset = Dataset.objects.get()
        self.assertEqual(dataset.uploaded_by, self.analyst)
        self.assertTrue(dataset.is_processed)
        self.assertTrue(dataset.decisions_generated)
        self.assertFalse(dataset.file)
        self.assertGreaterEqual(dataset.decisions.count(), 1)
        self.assertLessEqual(dataset.decisions.count(), 3)

    def test_missing_required_columns_are_rejected(self):
        self.client.force_login(self.analyst)
        response = self.client.post(
            self.upload_url,
            {
                "name": "Bad Sales",
                "type": "sales",
                "file": csv_upload("sales.csv", MISSING_COLUMN_SALES_CSV),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Dataset.objects.count(), 0)
        self.assertContains(response, "Missing required columns")


class OwnershipCharacterisationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password=PASSWORD,
            role="ANALYST",
        )
        self.other = User.objects.create_user(
            email="other@example.com",
            password=PASSWORD,
            role="ANALYST",
        )
        self.dataset = Dataset.objects.create(
            uploaded_by=self.owner,
            name="Owner Sales",
            type="sales",
            file="datasets/owner.csv",
        )
        Decision.objects.create(
            dataset=self.dataset,
            title="Revenue Risk",
            rule_name="SALES_REVENUE_HEALTH",
            domain="sales",
            recommendation="Review pricing.",
            explanation="Revenue is below threshold.",
            confidence=0.8,
        )

    def test_owner_can_open_dataset_detail(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("datasets:dataset_detail", args=[self.dataset.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_another_users_dataset_returns_404(self):
        self.client.force_login(self.other)
        response = self.client.get(
            reverse("datasets:dataset_detail", args=[self.dataset.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_another_users_dataset_decisions_return_404(self):
        self.client.force_login(self.other)
        response = self.client.get(
            reverse("decisions:list", args=[self.dataset.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_dataset_list_shows_only_own_datasets(self):
        Dataset.objects.create(
            uploaded_by=self.other,
            name="Other Sales",
            type="sales",
            file="datasets/other.csv",
        )
        self.client.force_login(self.other)
        response = self.client.get(reverse("datasets:dataset_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Other Sales")
        self.assertNotContains(response, "Owner Sales")
