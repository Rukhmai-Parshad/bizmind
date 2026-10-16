"""Tests for audit S8 (JWT part): lifetimes, rotation and blacklist."""
from datetime import timedelta

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from bizmind.testing import PASSWORD, make_user


class JwtSettingsTests(TestCase):
    def test_lifetimes_and_rotation_are_configured(self):
        jwt = settings.SIMPLE_JWT
        self.assertEqual(jwt["ACCESS_TOKEN_LIFETIME"], timedelta(minutes=15))
        self.assertEqual(jwt["REFRESH_TOKEN_LIFETIME"], timedelta(days=7))
        self.assertTrue(jwt["ROTATE_REFRESH_TOKENS"])
        self.assertTrue(jwt["BLACKLIST_AFTER_ROTATION"])

    def test_blacklist_app_is_installed(self):
        self.assertIn("rest_framework_simplejwt.token_blacklist", settings.INSTALLED_APPS)

    def test_no_project_migration_is_missing(self):
        # The blacklist tables come from the library's own migrations; our apps need none.
        call_command("makemigrations", "--check", "--dry-run", verbosity=0)


class JwtBehaviourTests(TestCase):
    def setUp(self):
        self.user = make_user("api@example.com")
        self.client = APIClient()

    def login(self):
        response = self.client.post("/api/auth/token/", {"email": "api@example.com", "password": PASSWORD})
        self.assertEqual(response.status_code, 200)
        return response.data

    def refresh(self, token):
        return self.client.post("/api/auth/token/refresh/", {"refresh": token})

    def test_issued_tokens_really_expire_after_15_minutes_and_7_days(self):
        tokens = self.login()
        access, refresh = AccessToken(tokens["access"]), RefreshToken(tokens["refresh"])
        self.assertEqual(access["exp"] - access["iat"], 15 * 60)
        self.assertEqual(refresh["exp"] - refresh["iat"], 7 * 24 * 60 * 60)

    def test_refreshing_returns_a_new_refresh_token(self):
        tokens = self.login()
        response = self.refresh(tokens["refresh"])
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertNotEqual(response.data["refresh"], tokens["refresh"])

    def test_the_old_refresh_token_stops_working_after_it_was_used(self):
        tokens = self.login()
        self.assertEqual(self.refresh(tokens["refresh"]).status_code, 200)
        reused = self.refresh(tokens["refresh"])  # e.g. a thief replaying a stolen token
        self.assertEqual(reused.status_code, 401)

    def test_the_new_refresh_token_works_and_chains_on(self):
        first = self.login()
        second = self.refresh(first["refresh"]).data
        third = self.refresh(second["refresh"])
        self.assertEqual(third.status_code, 200)

    def test_used_tokens_are_recorded_in_the_blacklist_table(self):
        tokens = self.login()
        self.refresh(tokens["refresh"])
        self.assertEqual(BlacklistedToken.objects.count(), 1)
        self.assertEqual(OutstandingToken.objects.filter(user=self.user).count(), 2)

    def test_an_expired_access_token_is_rejected(self):
        token = AccessToken.for_user(self.user)
        token.set_exp(lifetime=-timedelta(seconds=1))
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(self.client.get("/api/datasets/").status_code, 401)

    def test_a_fresh_access_token_is_accepted(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.login()['access']}")
        self.assertEqual(self.client.get("/api/datasets/").status_code, 200)

    def test_an_access_token_cannot_be_used_as_a_refresh_token(self):
        self.assertEqual(self.refresh(self.login()["access"]).status_code, 401)
