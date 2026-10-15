from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase

from accounts.models import User
from datasets.models import Dataset
from decisions.models import Decision

PASSWORD = "strong-password-123"

VALID_SALES_CSV = (
    "date,product,region,units_sold,unit_price\n"
    "2024-01-01,Widget,North,2,100\n"
)


def csv_upload(name, content):
    return SimpleUploadedFile(name, content.encode("utf-8"), content_type="text/csv")


class ApiLoginCharacterisationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="analyst@example.com",
            password=PASSWORD,
            role="ANALYST",
        )
        self.token_url = reverse("token_obtain_pair")

    def test_token_login_returns_access_and_refresh(self):
        response = self.client.post(
            self.token_url,
            {"email": "analyst@example.com", "password": PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_token_login_rejects_bad_password(self):
        response = self.client.post(
            self.token_url,
            {"email": "analyst@example.com", "password": "wrong-password"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_datasets_require_authentication(self):
        response = self.client.get(reverse("dataset-list"))
        self.assertEqual(response.status_code, 401)


class ApiUploadCharacterisationTests(APITestCase):
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

    def _authenticate(self, user):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {"email": user.email, "password": PASSWORD},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_analyst_can_upload_dataset_via_api(self):
        self._authenticate(self.analyst)
        response = self.client.post(
            reverse("dataset-list"),
            {
                "name": "API Sales",
                "type": "sales",
                "file": csv_upload("sales.csv", VALID_SALES_CSV),
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 201)
        dataset = Dataset.objects.get()
        self.assertEqual(dataset.uploaded_by, self.analyst)
        self.assertTrue(dataset.is_processed)

    def test_viewer_can_currently_upload_via_api(self):
        """Current behaviour (audit S1): the API does not block VIEWER uploads."""
        self._authenticate(self.viewer)
        response = self.client.post(
            reverse("dataset-list"),
            {
                "name": "Viewer Sales",
                "type": "sales",
                "file": csv_upload("sales.csv", VALID_SALES_CSV),
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Dataset.objects.get().uploaded_by, self.viewer)


class ApiOwnershipCharacterisationTests(APITestCase):
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
        self.decision = Decision.objects.create(
            dataset=self.dataset,
            title="Revenue Risk",
            rule_name="SALES_REVENUE_HEALTH",
            domain="sales",
            recommendation="Review pricing.",
            explanation="Revenue is below threshold.",
            confidence=0.8,
        )

    def _authenticate(self, user):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {"email": user.email, "password": PASSWORD},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_owner_can_retrieve_own_dataset(self):
        self._authenticate(self.owner)
        response = self.client.get(
            reverse("dataset-detail", args=[self.dataset.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.dataset.pk)

    def test_another_users_dataset_returns_404(self):
        self._authenticate(self.other)
        response = self.client.get(
            reverse("dataset-detail", args=[self.dataset.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_another_users_decision_returns_404(self):
        self._authenticate(self.other)
        response = self.client.get(
            reverse("decision-detail", args=[self.decision.pk])
        )
        self.assertEqual(response.status_code, 404)
