"""Tests for audit S4 (API part): throttling on the JWT token endpoints."""
from unittest import mock

from django.test import TestCase
from rest_framework.test import APIClient

from bizmind.testing import PASSWORD, RealCacheMixin, make_user

TOKEN_URL = "/api/auth/token/"
REFRESH_URL = "/api/auth/token/refresh/"


class TokenThrottleTests(RealCacheMixin, TestCase):
    def setUp(self):
        super().setUp()
        make_user("api@example.com")
        self.client = APIClient()

    def obtain(self, email="api@example.com", password="wrong", **extra):
        return self.client.post(TOKEN_URL, {"email": email, "password": password}, **extra)

    def test_five_attempts_per_minute_per_account_then_429_with_retry_after(self):
        for _ in range(5):
            self.assertEqual(self.obtain().status_code, 401)
        response = self.obtain()
        self.assertEqual(response.status_code, 429)
        self.assertIn("Retry-After", response)

    def test_a_throttled_account_cannot_log_in_even_with_the_right_password(self):
        for _ in range(5):
            self.obtain()
        self.assertEqual(self.obtain(password=PASSWORD).status_code, 429)

    def test_other_accounts_are_not_affected(self):
        make_user("second@example.com")
        for _ in range(5):
            self.obtain()
        self.assertEqual(self.obtain(email="second@example.com", password=PASSWORD).status_code, 200)

    def test_email_case_shares_one_counter(self):
        for _ in range(5):
            self.obtain(email="API@example.com")
        self.assertEqual(self.obtain(email="api@EXAMPLE.com").status_code, 429)

    def test_one_ip_is_limited_to_30_requests_per_minute_across_accounts(self):
        for number in range(30):
            self.assertEqual(self.obtain(email=f"nobody{number}@example.com").status_code, 401)
        self.assertEqual(self.obtain(email="nobody99@example.com").status_code, 429)

    def test_a_fake_x_forwarded_for_header_does_not_reset_the_ip_limit(self):
        for number in range(30):
            self.obtain(email=f"nobody{number}@example.com", HTTP_X_FORWARDED_FOR=f"1.1.1.{number}")
        response = self.obtain(email="nobody99@example.com", HTTP_X_FORWARDED_FOR="8.8.8.8")
        self.assertEqual(response.status_code, 429)

    def test_the_limit_ends_when_the_minute_is_over(self):
        for _ in range(5):
            self.obtain()
        self.assertEqual(self.obtain().status_code, 429)
        with mock.patch("rest_framework.throttling.SimpleRateThrottle.timer", return_value=10**10):
            self.assertEqual(self.obtain(password=PASSWORD).status_code, 200)

    def test_refresh_endpoint_is_throttled_per_ip(self):
        for _ in range(30):
            self.assertEqual(self.client.post(REFRESH_URL, {"refresh": "junk"}).status_code, 401)
        self.assertEqual(self.client.post(REFRESH_URL, {"refresh": "junk"}).status_code, 429)

    def test_normal_api_calls_are_not_throttled_by_the_login_limits(self):
        self.client.force_authenticate(make_user("reader@example.com"))
        for _ in range(40):
            self.assertEqual(self.client.get("/api/datasets/").status_code, 200)

    def test_a_normal_login_works(self):
        response = self.obtain(password=PASSWORD)
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
