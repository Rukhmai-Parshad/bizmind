"""Tests for audit S7: PATCH/PUT must not treat a dataset as its own duplicate.

Also covers a sibling bug found while fixing it: renaming a dataset to a name
the user already uses used to crash with HTTP 500 (database constraint).
"""
from django.test import RequestFactory, TestCase
from rest_framework.test import APIClient

from api.serializers import DatasetSerializer
from bizmind.testing import SALES_CSV, csv_upload, make_dataset, make_user
from datasets.models import Dataset

DUPLICATE = ["A dataset with this name and type already exists."]


class DatasetUpdateDuplicateCheckTests(TestCase):
    def setUp(self):
        self.user = make_user("analyst@example.com", "ANALYST")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.a = make_dataset(self.user, name="A", dataset_type="sales")
        self.b = make_dataset(self.user, name="B", dataset_type="sales")

    def patch(self, dataset, **fields):
        return self.client.patch(f"/api/datasets/{dataset.pk}/", fields, format="multipart")

    def test_patch_with_its_own_name_and_type_is_ok(self):
        self.assertEqual(self.patch(self.a, name="A", type="sales").status_code, 200)

    def test_patch_with_only_its_own_name_is_ok(self):
        self.assertEqual(self.patch(self.a, name="A").status_code, 200)

    def test_patch_with_only_its_own_type_is_ok(self):
        self.assertEqual(self.patch(self.a, type="sales").status_code, 200)

    def test_renaming_to_a_free_name_works_and_is_saved(self):
        response = self.patch(self.a, name="Renamed")
        self.assertEqual(response.status_code, 200)
        self.a.refresh_from_db()
        self.assertEqual(self.a.name, "Renamed")

    def test_renaming_to_another_datasets_name_is_a_400_not_a_500(self):
        response = self.patch(self.b, name="A")  # name-only: this used to crash with 500
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["name"], DUPLICATE)
        self.b.refresh_from_db()
        self.assertEqual(self.b.name, "B")

    def test_changing_the_type_into_a_collision_is_a_400(self):
        make_dataset(self.user, name="A", dataset_type="finance")
        response = self.patch(self.a, type="finance")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["name"], DUPLICATE)
        self.a.refresh_from_db()
        self.assertEqual(self.a.type, "sales")

    def test_same_name_with_a_different_type_is_allowed(self):
        self.assertEqual(self.patch(self.b, name="A", type="finance").status_code, 200)

    def test_another_users_dataset_with_the_same_name_does_not_block_a_rename(self):
        make_dataset(make_user("other@example.com"), name="Taken Elsewhere", dataset_type="sales")
        self.assertEqual(self.patch(self.a, name="Taken Elsewhere").status_code, 200)

    def test_creating_a_duplicate_is_still_rejected(self):
        response = self.client.post(
            "/api/datasets/",
            {"name": "A", "type": "sales", "file": csv_upload(SALES_CSV)},
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["name"], DUPLICATE)
        self.assertEqual(Dataset.objects.count(), 2)

    def test_full_update_validation_accepts_the_datasets_own_name_and_type(self):
        # PUT sends every field. Checked at serializer level so no file is stored.
        request = RequestFactory().put("/")
        request.user = self.user
        serializer = DatasetSerializer(
            self.a,
            data={"name": "A", "type": "sales", "file": csv_upload(SALES_CSV)},
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_full_update_validation_still_rejects_another_datasets_name(self):
        request = RequestFactory().put("/")
        request.user = self.user
        serializer = DatasetSerializer(
            self.b,
            data={"name": "A", "type": "sales", "file": csv_upload(SALES_CSV)},
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors["name"], DUPLICATE)
