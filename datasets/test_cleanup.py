"""Tests for audit S5: a failed upload must leave no row, no records and no file.

Same guarantees for the web view and the REST API, because both call
``save_and_process_dataset``.
"""
import os
from unittest import mock

from django.conf import settings
from django.test import TestCase
from rest_framework.test import APIClient

from bizmind.testing import SALES_CSV, TempMediaMixin, csv_upload, make_user, message_texts
from datasets.models import Dataset
from datasets.services import save_and_process_dataset
from decisions.models import Decision
from sales.models import SalesRecord

BAD_VALUE_CSV = "date,product,region,units_sold,unit_price\n2024-01-01,Laptop,North,0,50\n"
# Patched in to simulate a crash AFTER the records were already inserted.
CRASH_AFTER_RECORDS = mock.patch("sales.services.generate_decisions", side_effect=RuntimeError("boom"))


def stored_files():
    found = []
    for folder, _dirs, files in os.walk(settings.MEDIA_ROOT):
        found.extend(os.path.join(folder, name) for name in files)
    return found


class SaveAndProcessHelperTests(TempMediaMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user("analyst@example.com")

    def new_dataset(self, text=SALES_CSV, name="D"):
        return Dataset(uploaded_by=self.user, name=name, type="sales", file=csv_upload(text))

    def test_success_keeps_the_row_records_and_decisions_and_removes_the_file(self):
        dataset = self.new_dataset()
        with self.captureOnCommitCallbacks(execute=True):
            save_and_process_dataset(dataset)
        dataset.refresh_from_db()
        self.assertTrue(dataset.is_processed)
        self.assertEqual(SalesRecord.objects.count(), 2)
        self.assertEqual(Decision.objects.count(), 3)
        self.assertEqual(stored_files(), [])

    def test_bad_data_raises_the_original_error_and_leaves_nothing(self):
        with self.assertRaisesMessage(ValueError, "units_sold must be greater than zero."):
            save_and_process_dataset(self.new_dataset(BAD_VALUE_CSV))
        self.assertEqual(Dataset.objects.count(), 0)
        self.assertEqual(stored_files(), [])

    def test_crash_after_records_were_inserted_rolls_everything_back(self):
        with CRASH_AFTER_RECORDS, self.assertRaisesMessage(RuntimeError, "boom"):
            save_and_process_dataset(self.new_dataset())
        self.assertEqual(Dataset.objects.count(), 0)
        self.assertEqual(SalesRecord.objects.count(), 0)  # inserted, then rolled back
        self.assertEqual(Decision.objects.count(), 0)
        self.assertEqual(stored_files(), [])


class ApiFailureCleanupTests(TempMediaMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.client.force_authenticate(make_user("analyst@example.com"))

    def post(self, text):
        return self.client.post(
            "/api/datasets/",
            {"name": "X", "type": "sales", "file": csv_upload(text)},
            format="multipart",
        )

    def assert_nothing_left(self):
        self.assertEqual(Dataset.objects.count(), 0)
        self.assertEqual(SalesRecord.objects.count(), 0)
        self.assertEqual(stored_files(), [])

    def test_bad_value_in_csv_is_a_400_and_nothing_is_left(self):
        with self.assertLogs("api.views", level="WARNING"):
            response = self.post(BAD_VALUE_CSV)
        self.assertEqual(response.status_code, 400)
        self.assert_nothing_left()

    def test_unexpected_crash_is_a_json_500_with_a_safe_message_and_nothing_is_left(self):
        failing = APIClient(raise_request_exception=False)
        failing.force_authenticate(make_user("other@example.com"))
        with CRASH_AFTER_RECORDS, self.assertLogs("api.views", level="ERROR"):
            response = failing.post(
                "/api/datasets/",
                {"name": "X", "type": "sales", "file": csv_upload(SALES_CSV)},
                format="multipart",
            )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json()["detail"],
            "The dataset could not be processed because of an unexpected error.",
        )
        self.assertNotIn("boom", response.content.decode())  # internal error is not leaked
        self.assert_nothing_left()

    def test_user_can_retry_the_same_name_after_a_failure(self):
        with self.assertLogs("api.views", level="WARNING"):
            self.assertEqual(self.post(BAD_VALUE_CSV).status_code, 400)
        with self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(self.post(SALES_CSV).status_code, 201)


class WebFailureCleanupTests(TempMediaMixin, TestCase):
    def test_unexpected_crash_shows_a_generic_message_and_leaves_nothing(self):
        self.client.force_login(make_user("analyst@example.com"))
        with CRASH_AFTER_RECORDS, self.assertLogs("datasets.views", level="ERROR"):
            response = self.client.post(
                "/datasets/upload/",
                {"name": "X", "type": "sales", "file": csv_upload(SALES_CSV)},
            )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "The dataset could not be processed because of an unexpected error. "
            "Please try again or contact support.",
            message_texts(response),
        )
        self.assertEqual(Dataset.objects.count(), 0)
        self.assertEqual(SalesRecord.objects.count(), 0)
        self.assertEqual(stored_files(), [])
