"""Tests for audit S2: Sales/Marketing/Finance/Decision endpoints are read-only.

PRD: "any POST/PUT/PATCH/DELETE on record endpoints returns 405".
"""
from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from api.serializers import (
    FinanceRecordSerializer,
    MarketingRecordSerializer,
    SalesRecordSerializer,
)
from bizmind.testing import make_dataset, make_user
from decisions.models import Decision
from finance.models import FinanceRecord
from marketing.models import MarketingRecord
from sales.models import SalesRecord

READ_ONLY_ENDPOINTS = ("sales", "marketing", "finance", "decisions")
WRITE_METHODS = ("post", "put", "patch", "delete")


class RecordEndpointsAreReadOnlyTests(TestCase):
    def setUp(self):
        self.user = make_user("analyst@example.com", "ANALYST")
        self.dataset = make_dataset(self.user, name="Mine", is_processed=True)
        self.rows = {
            "sales": SalesRecord.objects.create(
                dataset=self.dataset, date=date(2024, 1, 1), product="P", region="R",
                units_sold=2, unit_price=10, revenue=20,
            ),
            "marketing": MarketingRecord.objects.create(
                dataset=self.dataset, date=date(2024, 1, 1), campaign="C", channel="Ch",
                impressions=10, clicks=1, conversions=0, spend=1, revenue=2,
            ),
            "finance": FinanceRecord.objects.create(
                dataset=self.dataset, date=date(2024, 1, 1), category="Cat",
                department="D", amount=5, type="income",
            ),
            "decisions": Decision.objects.create(
                dataset=self.dataset, title="T", rule_name="R", domain="sales",
                recommendation="r", explanation="e", confidence=0.5,
            ),
        }
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_every_write_method_on_every_record_endpoint_is_405(self):
        for endpoint in READ_ONLY_ENDPOINTS:
            urls = (f"/api/{endpoint}/", f"/api/{endpoint}/{self.rows[endpoint].pk}/")
            for url in urls:
                for method in WRITE_METHODS:
                    with self.subTest(url=url, method=method):
                        response = getattr(self.client, method)(url, {"dataset": self.dataset.pk}, format="json")
                        self.assertEqual(response.status_code, 405)

    def test_405_wins_over_ownership_so_nothing_leaks_about_other_users_rows(self):
        other = APIClient()
        other.force_authenticate(make_user("other@example.com"))
        response = other.delete(f"/api/sales/{self.rows['sales'].pk}/")
        self.assertEqual(response.status_code, 405)

    def test_failed_write_attempts_change_nothing(self):
        before = (SalesRecord.objects.count(), SalesRecord.objects.get().revenue)
        self.client.post("/api/sales/", {"revenue": 999}, format="json")
        self.client.patch(f"/api/sales/{self.rows['sales'].pk}/", {"revenue": 999}, format="json")
        self.client.delete(f"/api/sales/{self.rows['sales'].pk}/")
        self.assertEqual((SalesRecord.objects.count(), SalesRecord.objects.get().revenue), before)

    def test_reading_still_works_and_revenue_is_the_stored_server_value(self):
        for endpoint in READ_ONLY_ENDPOINTS:
            with self.subTest(endpoint=endpoint):
                self.assertEqual(self.client.get(f"/api/{endpoint}/").status_code, 200)
                self.assertEqual(
                    self.client.get(f"/api/{endpoint}/{self.rows[endpoint].pk}/").status_code, 200
                )
        self.assertEqual(self.client.get(f"/api/sales/{self.rows['sales'].pk}/").data["revenue"], 20.0)

    def test_dataset_endpoint_is_not_affected_and_still_lists(self):
        self.assertEqual(self.client.get("/api/datasets/").status_code, 200)


class RecordSerializersAreReadOnlyTests(TestCase):
    """Second line of defence: even if a write view is added later, no field is writable."""

    def test_every_field_of_every_record_serializer_is_read_only(self):
        for serializer_class in (
            SalesRecordSerializer, MarketingRecordSerializer, FinanceRecordSerializer
        ):
            for name, field in serializer_class().fields.items():
                with self.subTest(serializer=serializer_class.__name__, field=name):
                    self.assertTrue(field.read_only)

    def test_sales_revenue_cannot_be_supplied_by_the_client(self):
        self.assertTrue(SalesRecordSerializer().fields["revenue"].read_only)
        serializer = SalesRecordSerializer(data={"revenue": 999})
        serializer.is_valid()
        self.assertNotIn("revenue", serializer.validated_data)

    def test_the_openapi_schema_only_advertises_read_operations(self):
        schema = APIClient().get("/api/schema/", {"format": "json"}).json()
        for endpoint in ("sales", "marketing", "finance", "decisions"):
            with self.subTest(endpoint=endpoint):
                self.assertEqual(list(schema["paths"][f"/api/{endpoint}/"]), ["get"])
                self.assertEqual(list(schema["paths"][f"/api/{endpoint}/{{id}}/"]), ["get"])
