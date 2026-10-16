"""Characterisation tests: the REST API as it behaves today.

Several tests below pin behaviour that docs/00_Current_State_Audit.md lists as
a problem (S1, S2, S5, S7). They are named and commented as such. Milestone 1
fixes those on purpose, and each test must then be changed in the same commit.
"""
import os

from django.conf import settings
from django.test import TestCase
from rest_framework.test import APIClient

from bizmind.testing import (
    TempMediaMixin,
    PASSWORD,
    SALES_CSV,
    csv_upload,
    make_dataset,
    make_user,
)
from datasets.models import Dataset
from decisions.models import Decision
from finance.models import FinanceRecord
from marketing.models import MarketingRecord
from sales.models import SalesRecord

DATE = "2024-01-01"


def stored_files():
    found = []
    for folder, _dirs, files in os.walk(settings.MEDIA_ROOT):
        found.extend(os.path.join(folder, name) for name in files)
    return found


class TokenLoginTests(TestCase):
    def setUp(self):
        self.user = make_user("api@example.com")
        self.client = APIClient()

    def test_valid_credentials_return_access_and_refresh_tokens(self):
        response = self.client.post(
            "/api/auth/token/", {"email": "api@example.com", "password": PASSWORD}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_wrong_password_returns_401(self):
        response = self.client.post(
            "/api/auth/token/", {"email": "api@example.com", "password": "nope"}
        )
        self.assertEqual(response.status_code, 401)

    def test_access_token_works_as_a_bearer_token(self):
        token = self.client.post(
            "/api/auth/token/", {"email": "api@example.com", "password": PASSWORD}
        ).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(self.client.get("/api/datasets/").status_code, 200)

    def test_refresh_token_returns_a_new_access_token(self):
        refresh = self.client.post(
            "/api/auth/token/", {"email": "api@example.com", "password": PASSWORD}
        ).data["refresh"]
        response = self.client.post("/api/auth/token/refresh/", {"refresh": refresh})
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

    def test_requests_without_a_token_get_401(self):
        for url in (
            "/api/datasets/", "/api/sales/", "/api/marketing/",
            "/api/finance/", "/api/decisions/",
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 401)


class ApiUploadTests(TempMediaMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user("analyst@example.com", "ANALYST")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def upload(self, client=None, name="API Sales", dataset_type="sales",
               text=SALES_CSV, filename="data.csv"):
        with self.captureOnCommitCallbacks(execute=True):
            return (client or self.client).post(
                "/api/datasets/",
                {"name": name, "type": dataset_type, "file": csv_upload(text, filename)},
                format="multipart",
            )

    def test_analyst_upload_is_processed_and_returns_201(self):
        response = self.upload()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "API Sales")
        self.assertTrue(response.data["is_processed"])
        self.assertEqual(response.data["uploaded_by"]["email"], "analyst@example.com")

        dataset = Dataset.objects.get(name="API Sales")
        self.assertEqual(dataset.uploaded_by, self.user)
        self.assertEqual(SalesRecord.objects.filter(dataset=dataset).count(), 2)
        self.assertEqual(dataset.decisions.count(), 3)

    def test_stored_csv_is_deleted_after_processing(self):
        self.upload()
        self.assertEqual(stored_files(), [])

    def test_duplicate_name_and_type_returns_400(self):
        make_dataset(self.user, name="API Sales", dataset_type="sales")
        response = self.upload(name="API Sales")
        self.assertEqual(response.status_code, 400)
        self.assertIn("name", response.data)
        self.assertEqual(Dataset.objects.count(), 1)

    def test_list_is_paginated_and_only_shows_my_datasets(self):
        make_dataset(self.user, name="Mine")
        make_dataset(make_user("other@example.com"), name="Not mine")
        response = self.client.get("/api/datasets/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual([d["name"] for d in response.data["results"]], ["Mine"])

    # --- Audit S1 (fixed in Milestone 1): the API now applies the web rules ---

    def test_S1_viewer_gets_403_and_nothing_is_saved(self):
        viewer_client = APIClient()
        viewer_client.force_authenticate(make_user("viewer@example.com", "VIEWER"))
        response = self.upload(client=viewer_client, name="Viewer Upload")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Dataset.objects.count(), 0)
        self.assertEqual(stored_files(), [])

    def test_S1_non_csv_extension_is_rejected_by_the_api(self):
        response = self.upload(name="Text File", filename="data.txt")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["file"], ["Only CSV files are supported."])
        self.assertEqual(Dataset.objects.count(), 0)

    # --- Audit S5 (fixed in Milestone 1): processing failures clean up -------

    def test_S5_failed_processing_returns_400_and_leaves_nothing_behind(self):
        # Passes the upload validator (columns exist) but fails during processing.
        bad = "date,product,region,units_sold,unit_price\n2024-01-01,Laptop,North,0,50\n"
        with self.assertLogs("api.views", level="WARNING"):
            response = self.upload(name="Broken", text=bad)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["file"], ["units_sold must be greater than zero."])
        self.assertFalse(Dataset.objects.filter(name="Broken").exists())  # no row
        self.assertEqual(stored_files(), [])  # no file
        self.assertEqual(SalesRecord.objects.count(), 0)

    # --- Audit S7: PATCH trips over its own duplicate check --------------

    def test_S7_patching_name_and_type_of_a_dataset_to_its_own_values_works(self):
        # Fixed in Milestone 1: the dataset no longer counts as its own duplicate.
        dataset = make_dataset(self.user, name="Keep", dataset_type="sales")
        response = self.client.patch(
            f"/api/datasets/{dataset.pk}/",
            {"name": "Keep", "type": "sales"},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)

    def test_patching_only_the_name_works(self):
        dataset = make_dataset(self.user, name="Keep", dataset_type="sales")
        response = self.client.patch(
            f"/api/datasets/{dataset.pk}/", {"name": "Keep"}, format="multipart"
        )
        self.assertEqual(response.status_code, 200)


class ApiOwnershipTests(TestCase):
    """Another user's objects must return 404 on every endpoint."""

    def setUp(self):
        self.owner = make_user("owner@example.com")
        self.intruder = make_user("intruder@example.com")
        self.dataset = make_dataset(self.owner, name="Private", is_processed=True)
        self.sales = SalesRecord.objects.create(
            dataset=self.dataset, date=DATE, product="P", region="R",
            units_sold=1, unit_price=10, revenue=10,
        )
        self.marketing = MarketingRecord.objects.create(
            dataset=self.dataset, date=DATE, campaign="C", channel="Ch",
            impressions=10, clicks=1, conversions=0, spend=1, revenue=2,
        )
        self.finance = FinanceRecord.objects.create(
            dataset=self.dataset, date=DATE, category="Cat", department="D",
            amount=5, type="income",
        )
        self.decision = Decision.objects.create(
            dataset=self.dataset, title="T", rule_name="R", domain="sales",
            recommendation="r", explanation="e", confidence=0.5,
        )
        self.client = APIClient()

    def detail_urls(self):
        return {
            "dataset": f"/api/datasets/{self.dataset.pk}/",
            "sales": f"/api/sales/{self.sales.pk}/",
            "marketing": f"/api/marketing/{self.marketing.pk}/",
            "finance": f"/api/finance/{self.finance.pk}/",
            "decision": f"/api/decisions/{self.decision.pk}/",
        }

    def test_owner_can_read_every_object(self):
        self.client.force_authenticate(self.owner)
        for label, url in self.detail_urls().items():
            with self.subTest(label=label):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_other_user_gets_404_on_every_detail_endpoint(self):
        self.client.force_authenticate(self.intruder)
        for label, url in self.detail_urls().items():
            with self.subTest(label=label):
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_other_user_cannot_delete_or_modify_my_dataset(self):
        self.client.force_authenticate(self.intruder)
        url = f"/api/datasets/{self.dataset.pk}/"
        self.assertEqual(self.client.delete(url).status_code, 404)
        self.assertEqual(
            self.client.patch(url, {"type": "finance"}, format="multipart").status_code, 404
        )
        self.dataset.refresh_from_db()
        self.assertEqual(self.dataset.type, "sales")

    def test_other_user_sees_empty_lists(self):
        self.client.force_authenticate(self.intruder)
        for url in ("/api/datasets/", "/api/sales/", "/api/marketing/",
                    "/api/finance/", "/api/decisions/"):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).data["count"], 0)

    def test_dataset_query_filter_cannot_reach_another_users_records(self):
        self.client.force_authenticate(self.intruder)
        response = self.client.get(f"/api/sales/?dataset={self.dataset.pk}")
        self.assertEqual(response.data["count"], 0)

    def test_creating_a_record_in_another_users_dataset_is_405(self):
        # Record endpoints are read-only (S2), so there is nothing to create.
        self.client.force_authenticate(self.intruder)
        response = self.client.post(
            "/api/sales/",
            {"dataset": self.dataset.pk, "date": DATE, "product": "X", "region": "Y",
             "units_sold": 1, "unit_price": 1, "revenue": 1},
            format="json",
        )
        self.assertEqual(response.status_code, 405)
        self.assertEqual(SalesRecord.objects.count(), 1)


class ApiRecordEndpointTests(TestCase):
    """Audit S2 (fixed in Milestone 1): record endpoints are read-only."""

    def setUp(self):
        self.user = make_user("analyst@example.com")
        self.dataset = make_dataset(self.user, name="Mine", is_processed=True)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_decisions_endpoint_is_read_only(self):
        response = self.client.post(
            "/api/decisions/",
            {"dataset": self.dataset.pk, "title": "x", "rule_name": "x", "domain": "sales",
             "recommendation": "x", "explanation": "x", "confidence": 0.5},
            format="json",
        )
        self.assertEqual(response.status_code, 405)

    def test_S2_sales_record_cannot_be_created_even_with_a_client_supplied_revenue(self):
        response = self.client.post(
            "/api/sales/",
            {"dataset": self.dataset.pk, "date": DATE, "product": "P", "region": "R",
             "units_sold": 2, "unit_price": 10, "revenue": 999},
            format="json",
        )
        self.assertEqual(response.status_code, 405)
        self.assertEqual(SalesRecord.objects.count(), 0)

    def test_S2_sales_record_cannot_be_edited_or_deleted(self):
        record = SalesRecord.objects.create(
            dataset=self.dataset, date=DATE, product="P", region="R",
            units_sold=1, unit_price=10, revenue=10,
        )
        patched = self.client.patch(f"/api/sales/{record.pk}/", {"product": "Changed"}, format="json")
        deleted = self.client.delete(f"/api/sales/{record.pk}/")
        self.assertEqual((patched.status_code, deleted.status_code), (405, 405))
        record.refresh_from_db()
        self.assertEqual(record.product, "P")

    def test_S2_marketing_and_finance_records_cannot_be_created(self):
        marketing = self.client.post("/api/marketing/", {"dataset": self.dataset.pk}, format="json")
        finance = self.client.post("/api/finance/", {"dataset": self.dataset.pk}, format="json")
        self.assertEqual((marketing.status_code, finance.status_code), (405, 405))


class ApiDocsTests(TestCase):
    def test_openapi_schema_and_swagger_page_load_without_login(self):
        client = APIClient()
        self.assertEqual(client.get("/api/schema/").status_code, 200)
        self.assertEqual(client.get("/api/docs/").status_code, 200)
