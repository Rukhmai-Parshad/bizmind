"""Self-service account deletion (DPDP Act 2023: right to erasure)."""
import os
from datetime import date

from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.files.base import ContentFile
from django.test import Client, TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from accounts import ratelimit
from accounts.models import User
from bizmind.testing import PASSWORD, RealCacheMixin, TempMediaMixin, make_dataset, make_user, message_texts
from datasets.models import Dataset
from decisions.models import Decision
from finance.models import FinanceRecord
from marketing.models import MarketingRecord
from sales.models import SalesRecord

SETTINGS_URL = "/accounts/settings/"
DELETE_URL = "/accounts/settings/delete/"
GOOD = {"password": PASSWORD, "confirm": "on"}


def add_everything(user, name="Mine"):
    """One dataset with a row of every kind plus a decision, and a leftover stored file."""
    dataset = Dataset.objects.create(
        uploaded_by=user, name=name, type="sales", is_processed=True,
        file=ContentFile(b"date,product\n", name=f"{name}.csv"),
    )
    SalesRecord.objects.create(dataset=dataset, date=date(2024, 1, 1), product="P", region="R", units_sold=1, unit_price=1, revenue=1)
    MarketingRecord.objects.create(dataset=dataset, date=date(2024, 1, 1), campaign="C", channel="Ch", impressions=1, clicks=1, conversions=0, spend=1, revenue=1)
    FinanceRecord.objects.create(dataset=dataset, date=date(2024, 1, 1), category="Cat", department="D", amount=1, type="income")
    Decision.objects.create(dataset=dataset, title="T", rule_name="R", domain="sales", recommendation="r", explanation="e", confidence=0.5)
    return dataset


def stored_files():
    return [os.path.join(d, f) for d, _s, fs in os.walk(settings.MEDIA_ROOT) for f in fs]


class SettingsPageTests(TestCase):
    def setUp(self):
        self.user = make_user("analyst@example.com", "ANALYST")

    def test_login_is_required(self):
        for url in (SETTINGS_URL, DELETE_URL):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response["Location"].startswith("/accounts/login/"))

    def test_settings_shows_what_is_held_about_the_user(self):
        self.client.force_login(self.user)
        make_dataset(self.user, "One")
        html = self.client.get(SETTINGS_URL).content.decode()
        for text in ("analyst@example.com", "Analyst", "Account created", "Consent given",
                     "Not recorded. This account was created before consent was recorded.", "Datasets"):
            self.assertIn(text, html)
        self.assertIn(f'href="{DELETE_URL}"', html)

    def test_settings_shows_the_consent_time_when_it_exists(self):
        from django.utils import timezone
        self.user.consented_at = timezone.now()
        self.user.save()
        self.client.force_login(self.user)
        html = self.client.get(SETTINGS_URL).content.decode()
        self.assertIn("UTC, to the Terms and Privacy Policy", html)

    def test_the_sidebar_links_to_settings_for_every_role(self):
        for role in ("ADMIN", "ANALYST", "VIEWER"):
            with self.subTest(role=role):
                client = Client()
                client.force_login(make_user(f"{role.lower()}-side@example.com", role))
                self.assertIn('href="/accounts/settings/"', client.get("/dashboard/").content.decode())

    def test_the_settings_link_is_marked_as_current_on_its_pages(self):
        self.client.force_login(self.user)
        self.assertIn('href="/accounts/settings/" aria-current="page"', self.client.get(SETTINGS_URL).content.decode())

    def test_confirmation_page_explains_and_does_not_delete_on_get(self):
        self.client.force_login(self.user)
        response = self.client.get(DELETE_URL)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("What will be deleted", html)
        self.assertIn("csrfmiddlewaretoken", html)
        self.assertIn('type="checkbox" name="confirm"', html)
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())


class DeletionRulesTests(TempMediaMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user("leaving@example.com", "ANALYST")
        self.other = make_user("staying@example.com", "ANALYST")
        self.client.force_login(self.user)

    def post(self, data=None, client=None):
        return (client or self.client).post(DELETE_URL, GOOD if data is None else data)

    def test_wrong_password_deletes_nothing(self):
        response = self.post({"password": "wrong-password", "confirm": "on"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("That password is not correct.", response.context["form"].errors["password"])
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_missing_confirmation_tick_deletes_nothing(self):
        response = self.post({"password": PASSWORD})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Tick the box to confirm", response.context["form"].errors["confirm"][0])
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_the_form_needs_a_csrf_token(self):
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.user)
        response = strict.post(DELETE_URL, GOOD)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_deleting_removes_the_account_and_everything_it_owns(self):
        mine = add_everything(self.user)
        add_everything(self.other, "Theirs")
        with self.captureOnCommitCallbacks(execute=True):
            response = self.post()
        self.assertRedirects(response, "/", fetch_redirect_response=False)
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())
        self.assertFalse(Dataset.objects.filter(pk=mine.pk).exists())
        for model in (SalesRecord, MarketingRecord, FinanceRecord, Decision):
            with self.subTest(model=model.__name__):
                self.assertEqual(model.objects.filter(dataset__uploaded_by__email="leaving@example.com").count(), 0)
                self.assertEqual(model.objects.count(), 1)  # the other user's row is untouched

    def test_other_users_data_is_not_touched(self):
        theirs = add_everything(self.other, "Theirs")
        add_everything(self.user)
        with self.captureOnCommitCallbacks(execute=True):
            self.post()
        self.assertTrue(Dataset.objects.filter(pk=theirs.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.other.pk).exists())
        self.assertEqual(Decision.objects.filter(dataset=theirs).count(), 1)

    def test_stored_files_left_on_disk_are_deleted_but_not_other_users_files(self):
        add_everything(self.user)
        add_everything(self.other, "Theirs")
        self.assertEqual(len(stored_files()), 2)
        with self.captureOnCommitCallbacks(execute=True):
            self.post()
        remaining = stored_files()
        self.assertEqual(len(remaining), 1)
        self.assertIn("Theirs", remaining[0])

    def test_the_user_is_logged_out_and_told(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.post()
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertIn("Your account and all its data have been deleted.", message_texts(response))
        self.assertEqual(self.client.get("/dashboard/").status_code, 302)

    def test_login_sessions_on_other_devices_are_removed(self):
        other_device = Client()
        other_device.force_login(self.user)
        neighbour = Client()
        neighbour.force_login(self.other)
        self.assertEqual(Session.objects.count(), 3)
        with self.captureOnCommitCallbacks(execute=True):
            self.post()
        self.assertEqual(Session.objects.count(), 1)  # only the other user's session remains
        self.assertEqual(other_device.get("/dashboard/").status_code, 302)

    def test_api_refresh_token_records_and_the_blacklist_are_removed(self):
        api = APIClient()
        tokens = api.post("/api/auth/token/", {"email": "leaving@example.com", "password": PASSWORD}).data
        api.post("/api/auth/token/refresh/", {"refresh": tokens["refresh"]})  # rotation blacklists the first one
        APIClient().post("/api/auth/token/", {"email": "staying@example.com", "password": PASSWORD})
        self.assertEqual(OutstandingToken.objects.filter(user=self.user).count(), 2)
        self.assertEqual(BlacklistedToken.objects.count(), 1)
        with self.captureOnCommitCallbacks(execute=True):
            self.post()
        self.assertEqual(OutstandingToken.objects.filter(user__isnull=True).count(), 0)
        self.assertEqual(OutstandingToken.objects.count(), 1)  # only the other user's token
        self.assertEqual(BlacklistedToken.objects.count(), 0)

    def test_the_email_can_be_used_to_sign_up_again_afterwards(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.post()
        response = self.client.post("/accounts/signup/", {"email": "leaving@example.com", "password": "longenough1", "consent": "on"})
        self.assertRedirects(response, "/accounts/login/", fetch_redirect_response=False)

    def test_every_role_can_delete_its_own_account(self):
        for role in ("ADMIN", "ANALYST", "VIEWER"):
            with self.subTest(role=role):
                user = make_user(f"{role.lower()}-x@example.com", role)
                client = Client()
                client.force_login(user)
                with self.captureOnCommitCallbacks(execute=True):
                    self.post(client=client)
                self.assertFalse(User.objects.filter(pk=user.pk).exists())

    def test_staff_accounts_cannot_be_deleted_here(self):
        staff = User.objects.create_superuser(email="root@example.com", password=PASSWORD)
        client = Client()
        client.force_login(staff)
        page = client.get(SETTINGS_URL).content.decode()
        self.assertNotIn(f'href="{DELETE_URL}"', page)
        self.assertIn("Staff accounts cannot be deleted here", page)
        response = client.post(DELETE_URL, GOOD)
        self.assertRedirects(response, SETTINGS_URL, fetch_redirect_response=False)
        self.assertTrue(User.objects.filter(pk=staff.pk).exists())


class DeletionRateLimitTests(RealCacheMixin, TestCase):
    def test_repeated_wrong_passwords_are_blocked_like_logins(self):
        user = make_user("leaving@example.com")
        self.client.force_login(user)
        for _ in range(ratelimit.LOGIN_MAX_FAILURES_PER_EMAIL_AND_IP):
            self.assertEqual(self.client.post(DELETE_URL, {"password": "nope", "confirm": "on"}).status_code, 200)
        response = self.client.post(DELETE_URL, GOOD)  # even the right password is refused now
        self.assertEqual(response.status_code, 429)
        self.assertTrue(User.objects.filter(pk=user.pk).exists())
