"""Tests for the shared upload validator (audit S1).

The same rules must apply to the web form and to the REST API, so most
tests here run the SAME bad file through both and compare.
"""
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from bizmind.testing import (
    SALES_CSV,
    TempMediaMixin,
    csv_upload,
    make_user,
)
from datasets.models import Dataset
from datasets.validators import (
    MAX_ROWS,
    MAX_UPLOAD_BYTES,
    can_upload,
    validate_csv_upload,
)

HEADER = "date,product,region,units_sold,unit_price\n"


def sales_rows(count):
    return HEADER + "2024-01-01,Laptop,North,1,10\n" * count


def upload(text, name="data.csv"):
    return SimpleUploadedFile(name, text.encode("utf-8"), content_type="text/csv")


class ValidatorUnitTests(SimpleTestCase):
    def assert_rejected(self, file, dataset_type, expected):
        with self.assertRaises(ValidationError) as caught:
            validate_csv_upload(file, dataset_type)
        self.assertEqual(caught.exception.messages, [expected])

    def test_valid_file_passes_and_is_rewound(self):
        file = upload(SALES_CSV)
        validate_csv_upload(file, "sales")
        self.assertEqual(file.read(), SALES_CSV.encode())  # position reset to 0

    def test_extension_must_be_csv_in_any_letter_case(self):
        self.assert_rejected(upload(SALES_CSV, "data.txt"), "sales", "Only CSV files are supported.")
        validate_csv_upload(upload(SALES_CSV, "DATA.CSV"), "sales")

    def test_size_limit_is_10_mb(self):
        self.assertEqual(MAX_UPLOAD_BYTES, 10 * 1024 * 1024)
        big = upload(SALES_CSV)
        big.size = MAX_UPLOAD_BYTES + 1
        self.assert_rejected(big, "sales", "CSV file must be 10 MB or smaller.")

    def test_row_limit_is_50000_rows_inclusive(self):
        self.assertEqual(MAX_ROWS, 50_000)
        validate_csv_upload(upload(sales_rows(50_000)), "sales")
        self.assert_rejected(
            upload(sales_rows(50_001)),
            "sales",
            "CSV has 50,001 rows; the limit is 50,000 rows per file.",
        )

    def test_missing_columns_are_named_in_sorted_order(self):
        self.assert_rejected(
            upload("date,product\n2024-01-01,Laptop\n"),
            "sales",
            "Missing required columns: region, unit_price, units_sold",
        )

    def test_required_columns_depend_on_the_dataset_type(self):
        self.assert_rejected(
            upload(SALES_CSV),
            "finance",
            "Missing required columns: amount, category, department, type",
        )

    def test_duplicate_column_names_are_rejected(self):
        file = upload(HEADER.strip() + ",Product\n2024-01-01,A,N,1,1,A\n")
        with self.assertRaisesMessage(ValidationError, "duplicate column names"):
            validate_csv_upload(file, "sales")

    def test_headers_are_trimmed_lowercased_and_bom_tolerated(self):
        text = "\ufeff Date , PRODUCT,Region,Units_Sold,Unit_Price\n2024-01-01,A,N,1,1\n"
        validate_csv_upload(upload(text), "sales")


class CanUploadRoleTests(TestCase):
    def test_admin_and_analyst_may_upload_but_viewer_may_not(self):
        self.assertTrue(can_upload(make_user("a@example.com", "ADMIN")))
        self.assertTrue(can_upload(make_user("b@example.com", "ANALYST")))
        self.assertFalse(can_upload(make_user("c@example.com", "VIEWER")))

    def test_anonymous_user_may_not_upload(self):
        from django.contrib.auth.models import AnonymousUser

        self.assertFalse(can_upload(AnonymousUser()))


class WebAndApiShareTheSameRules(TempMediaMixin, TestCase):
    """The same bad file must be refused with the same message in both places."""

    BAD_FILES = {
        "not_csv": (SALES_CSV, "data.txt"),
        "missing_columns": ("date,product\n2024-01-01,A\n", "data.csv"),
        "too_many_rows": (sales_rows(50_001), "data.csv"),
        "duplicate_columns": (HEADER.strip() + ",Product\n2024-01-01,A,N,1,1,A\n", "data.csv"),
    }

    def setUp(self):
        super().setUp()
        self.user = make_user("analyst@example.com", "ANALYST")

    def web_errors(self, text, filename):
        self.client.force_login(self.user)
        response = self.client.post(
            "/datasets/upload/",
            {"name": "X", "type": "sales", "file": csv_upload(text, filename)},
        )
        self.assertEqual(response.status_code, 200)
        return response.context["form"].errors["file"]

    def api_errors(self, text, filename):
        client = APIClient()
        client.force_authenticate(self.user)
        response = client.post(
            "/api/datasets/",
            {"name": "X", "type": "sales", "file": csv_upload(text, filename)},
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)
        return response.data["file"]

    def test_same_bad_file_gets_the_same_message_from_web_and_api(self):
        for label, (text, filename) in self.BAD_FILES.items():
            with self.subTest(case=label):
                web = self.web_errors(text, filename)
                api = self.api_errors(text, filename)
                self.assertEqual([str(m) for m in web], [str(m) for m in api])

    def test_nothing_is_saved_when_the_api_rejects_a_file(self):
        for label, (text, filename) in self.BAD_FILES.items():
            with self.subTest(case=label):
                self.api_errors(text, filename)
                self.assertEqual(Dataset.objects.count(), 0)

    def test_web_form_rejects_more_than_50000_rows(self):
        self.assertIn(
            "CSV has 50,001 rows; the limit is 50,000 rows per file.",
            self.web_errors(sales_rows(50_001), "data.csv"),
        )


class ApiRoleTests(TempMediaMixin, TestCase):
    """PRD: a viewer (web or API) who tries to upload is refused; API gives 403."""

    def setUp(self):
        super().setUp()
        self.viewer = make_user("viewer@example.com", "VIEWER")
        self.client = APIClient()

    def post_upload(self, client):
        return client.post(
            "/api/datasets/",
            {"name": "X", "type": "sales", "file": csv_upload(SALES_CSV)},
            format="multipart",
        )

    def test_viewer_upload_returns_403_with_a_clear_message(self):
        self.client.force_authenticate(self.viewer)
        response = self.post_upload(self.client)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["detail"], "Your account has read-only access.")
        self.assertEqual(Dataset.objects.count(), 0)

    def test_role_is_checked_before_the_file_so_a_bad_file_is_still_403(self):
        self.client.force_authenticate(self.viewer)
        response = self.client.post(
            "/api/datasets/",
            {"name": "X", "type": "sales", "file": csv_upload("junk", "x.txt")},
            format="multipart",
        )
        self.assertEqual(response.status_code, 403)

    def test_anonymous_upload_is_401_not_403(self):
        self.assertEqual(self.post_upload(self.client).status_code, 401)

    def test_viewer_may_still_read_the_api(self):
        self.client.force_authenticate(self.viewer)
        self.assertEqual(self.client.get("/api/datasets/").status_code, 200)

    def test_viewer_cannot_delete_or_patch_even_their_own_dataset(self):
        from bizmind.testing import make_dataset

        dataset = make_dataset(self.viewer, name="Mine")
        self.client.force_authenticate(self.viewer)
        self.assertEqual(self.client.delete(f"/api/datasets/{dataset.pk}/").status_code, 403)
        patched = self.client.patch(
            f"/api/datasets/{dataset.pk}/", {"name": "New"}, format="multipart"
        )
        self.assertEqual(patched.status_code, 403)
        self.assertTrue(Dataset.objects.filter(pk=dataset.pk, name="Mine").exists())

    def test_admin_and_analyst_can_upload_through_the_api(self):
        for email, role in (("admin@example.com", "ADMIN"), ("an@example.com", "ANALYST")):
            with self.subTest(role=role), self.captureOnCommitCallbacks(execute=True):
                client = APIClient()
                client.force_authenticate(make_user(email, role))
                response = client.post(
                    "/api/datasets/",
                    {"name": f"By {role}", "type": "sales", "file": csv_upload(SALES_CSV)},
                    format="multipart",
                )
                self.assertEqual(response.status_code, 201)
