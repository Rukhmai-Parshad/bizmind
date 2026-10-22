"""Consent at signup, proof of consent, and data minimisation (DPDP Act 2023)."""
import logging
from datetime import timedelta

from django.contrib.sessions.models import Session  # noqa: F401  (kept for symmetry with deletion tests)
from django.core.management import call_command
from django.db.migrations.loader import MigrationLoader
from django.db import connection
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from bizmind.testing import PASSWORD, SALES_CSV, TempMediaMixin, csv_upload, make_user

CONSENT_ERROR = (
    "You must confirm that you are 18 or older and agree to the Terms "
    "and Privacy Policy to create an account."
)
VALID = {"email": "new@example.com", "password": "longenough1"}


class ConsentCheckboxTests(TestCase):
    def post(self, **extra):
        return self.client.post("/accounts/signup/", {**VALID, **extra})

    def test_the_checkbox_is_shown_required_and_unticked_with_links(self):
        html = self.client.get("/accounts/signup/").content.decode()
        self.assertIn('type="checkbox" name="consent" id="id_consent" required>', html)
        self.assertNotIn("checked", html.split('id="id_consent"')[1].split(">")[0])
        self.assertIn("I am 18 or older and agree to the", html)
        label = html.split('for="id_consent"')[1].split("</label>")[0]
        self.assertIn('href="/terms/"', label)
        self.assertIn('href="/privacy/"', label)

    def test_signup_without_ticking_is_refused_with_a_clear_error(self):
        response = self.post()  # box not sent at all, like an unticked box
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].errors["consent"], [CONSENT_ERROR])
        self.assertContains(response, CONSENT_ERROR)
        self.assertContains(response, "has-error")
        self.assertFalse(User.objects.filter(email="new@example.com").exists())

    def test_an_empty_or_false_value_does_not_count_as_consent(self):
        for value in ("", "false"):  # a browser omits an unticked box entirely
            with self.subTest(value=value):
                response = self.post(consent=value)
                self.assertEqual(response.status_code, 200)
                self.assertFalse(User.objects.exists())

    def test_ticking_creates_the_account_and_stores_proof_of_consent(self):
        before = timezone.now()
        response = self.post(consent="on")
        after = timezone.now()
        self.assertRedirects(response, "/accounts/login/", fetch_redirect_response=False)
        user = User.objects.get(email="new@example.com")
        self.assertIsNotNone(user.consented_at)
        self.assertTrue(timezone.is_aware(user.consented_at))
        self.assertTrue(before - timedelta(seconds=1) <= user.consented_at <= after + timedelta(seconds=1))

    def test_the_checkbox_stays_unticked_after_other_errors(self):
        response = self.client.post("/accounts/signup/", {"email": "bad", "password": "x"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("checked", response.content.decode().split('id="id_consent"')[1].split(">")[0])

    def test_other_errors_do_not_create_a_consent_record(self):
        self.post(email="not-an-email", consent="on")
        self.assertEqual(User.objects.count(), 0)

    def test_consented_at_is_empty_for_accounts_made_without_the_form(self):
        self.assertIsNone(make_user("legacy@example.com").consented_at)
        root = User.objects.create_superuser(email="root@example.com", password=PASSWORD)
        self.assertIsNone(root.consented_at)

    def test_consent_is_shown_read_only_in_the_admin(self):
        from django.contrib import admin
        model_admin = admin.site._registry[User]
        self.assertIn("consented_at", model_admin.readonly_fields)


class MigrationTests(TestCase):
    def test_the_new_migration_is_the_latest_and_nothing_else_is_pending(self):
        loader = MigrationLoader(connection)
        leaves = [name for app, name in loader.graph.leaf_nodes() if app == "accounts"]
        self.assertEqual(leaves, ["0004_consent_and_data_minimisation"])
        call_command("makemigrations", "--check", "--dry-run", verbosity=0)

    def test_existing_migrations_are_still_there_unchanged_in_name(self):
        loader = MigrationLoader(connection)
        names = {name for app, name in loader.disk_migrations if app == "accounts"}
        self.assertTrue({"0001_initial", "0003_alter_user_managers"} <= names)


class DataMinimisationTests(TempMediaMixin, TestCase):
    """Only the personal data the app really needs is stored."""

    EXPECTED_USER_FIELDS = {
        "id", "password", "is_superuser", "email", "is_staff", "is_active",
        "date_joined", "role", "consented_at", "groups", "user_permissions",
    }

    def test_the_user_model_holds_exactly_the_audited_fields(self):
        names = {field.name for field in User._meta.get_fields() if not field.auto_created or field.name == "id"}
        names -= {f.name for f in User._meta.get_fields() if f.auto_created and f.name != "id"}
        self.assertEqual(names, self.EXPECTED_USER_FIELDS)

    def test_no_name_or_login_time_columns_exist(self):
        columns = {c.name for c in connection.introspection.get_table_description(connection.cursor(), User._meta.db_table)}
        for removed in ("first_name", "last_name", "last_login"):
            self.assertNotIn(removed, columns)

    def test_logging_in_still_works_without_a_last_login_column(self):
        user = make_user("a@example.com")
        self.assertTrue(self.client.login(email="a@example.com", password=PASSWORD))
        response = self.client.post("/accounts/login/", {"email": "a@example.com", "password": PASSWORD})
        self.assertEqual(response.status_code, 302)
        token = APIClient().post("/api/auth/token/", {"email": "a@example.com", "password": PASSWORD})
        self.assertEqual(token.status_code, 200)
        user.refresh_from_db()  # no error: the user row is intact

    def test_admin_login_still_works_for_staff(self):
        User.objects.create_superuser(email="root@example.com", password=PASSWORD)
        response = self.client.post("/admin/login/", {"username": "root@example.com", "password": PASSWORD})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get("/admin/").status_code, 200)

    def test_the_api_user_object_has_no_name_fields(self):
        user = make_user("owner@example.com")
        client = APIClient()
        client.force_authenticate(user)
        with self.captureOnCommitCallbacks(execute=True):
            response = client.post("/api/datasets/", {"name": "D", "type": "sales", "file": csv_upload(SALES_CSV)}, format="multipart")
        self.assertEqual(set(response.data["uploaded_by"]), {"id", "email", "role"})

    def test_error_logs_do_not_contain_the_dataset_name(self):
        user = make_user("analyst@example.com")
        self.client.force_login(user)
        bad = "date,product,region,units_sold,unit_price\n2024-01-01,Laptop,North,0,50\n"
        with self.assertLogs("datasets.views", level=logging.WARNING) as logs:
            self.client.post("/datasets/upload/", {"name": "Secret Customer Report", "type": "sales", "file": csv_upload(bad)})
        text = " ".join(logs.output)
        self.assertNotIn("Secret Customer Report", text)
        self.assertIn(f"user_id={user.pk}", text)
        self.assertIn("type=sales", text)

    def test_api_error_logs_do_not_contain_the_dataset_name(self):
        user = make_user("analyst@example.com")
        client = APIClient()
        client.force_authenticate(user)
        bad = "date,product,region,units_sold,unit_price\n2024-01-01,Laptop,North,0,50\n"
        with self.assertLogs("api.views", level=logging.WARNING) as logs:
            client.post("/api/datasets/", {"name": "Secret Customer Report", "type": "sales", "file": csv_upload(bad)}, format="multipart")
        self.assertNotIn("Secret Customer Report", " ".join(logs.output))

    def test_the_upload_page_asks_people_not_to_upload_personal_data(self):
        self.client.force_login(make_user("analyst@example.com"))
        html = self.client.get("/datasets/upload/").content.decode()
        self.assertIn("leave out personal data about individuals", html)
