"""Tests for audit S4 (web part): rate limiting on login and signup."""
from django.test import TestCase, override_settings

from accounts import ratelimit
from accounts.models import User
from bizmind.testing import PASSWORD, RealCacheMixin, make_user

BLOCKED = ratelimit.LOGIN_BLOCKED_MESSAGE


class LoginRateLimitTests(RealCacheMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user("victim@example.com")

    def attempt(self, email="victim@example.com", password="wrong-password", ip="10.0.0.1"):
        return self.client.post(
            "/accounts/login/", {"email": email, "password": password}, REMOTE_ADDR=ip
        )

    def test_five_failures_are_allowed_then_the_sixth_attempt_is_blocked(self):
        for _ in range(ratelimit.LOGIN_MAX_FAILURES_PER_EMAIL_AND_IP):
            self.assertEqual(self.attempt().status_code, 200)  # normal "Invalid email or password."
        response = self.attempt()
        self.assertEqual(response.status_code, 429)
        self.assertIn(BLOCKED, response.context["form"].non_field_errors())

    def test_while_blocked_even_the_correct_password_does_not_log_in(self):
        for _ in range(5):
            self.attempt()
        response = self.attempt(password=PASSWORD)
        self.assertEqual(response.status_code, 429)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_a_different_account_from_the_same_ip_is_not_blocked(self):
        make_user("other@example.com")
        for _ in range(5):
            self.attempt()
        response = self.attempt(email="other@example.com", password=PASSWORD)
        self.assertEqual(response.status_code, 302)  # logged in

    def test_the_real_owner_on_another_ip_can_still_log_in(self):
        # A stranger's 5 failures must not lock the owner out (no easy lockout).
        for _ in range(5):
            self.attempt(ip="203.0.113.9")
        response = self.attempt(password=PASSWORD, ip="198.51.100.7")
        self.assertEqual(response.status_code, 302)

    def test_email_case_does_not_give_a_fresh_set_of_attempts(self):
        for _ in range(5):
            self.attempt(email="VICTIM@example.com")
        self.assertEqual(self.attempt(email="victim@EXAMPLE.com").status_code, 429)

    def test_one_ip_trying_many_accounts_is_blocked_after_20_failures(self):
        for number in range(ratelimit.LOGIN_MAX_FAILURES_PER_IP):
            self.attempt(email=f"user{number}@example.com")
        response = self.attempt(password=PASSWORD)  # the real user, same IP
        self.assertEqual(response.status_code, 429)

    def test_one_account_attacked_from_many_ips_is_blocked_after_20_failures(self):
        for number in range(ratelimit.LOGIN_MAX_FAILURES_PER_EMAIL):
            self.attempt(ip=f"10.1.0.{number}")
        response = self.attempt(password=PASSWORD, ip="10.9.9.9")  # a brand new address
        self.assertEqual(response.status_code, 429)

    def test_a_successful_login_resets_the_email_and_ip_counter(self):
        for _ in range(4):
            self.attempt()
        self.assertEqual(self.attempt(password=PASSWORD).status_code, 302)
        self.client.post("/accounts/logout/")
        for _ in range(4):  # 4 more failures are fine: the counter started again
            self.assertEqual(self.attempt().status_code, 200)
        self.assertEqual(self.attempt(password=PASSWORD).status_code, 302)

    def test_opening_the_login_page_is_never_counted(self):
        for _ in range(30):
            self.assertEqual(self.client.get("/accounts/login/", REMOTE_ADDR="10.0.0.1").status_code, 200)
        self.assertEqual(self.attempt(password=PASSWORD).status_code, 302)

    def test_x_forwarded_for_cannot_be_used_to_dodge_the_limit_by_default(self):
        for number in range(5):
            self.client.post(
                "/accounts/login/",
                {"email": "victim@example.com", "password": "wrong-password"},
                REMOTE_ADDR="10.0.0.1",
                HTTP_X_FORWARDED_FOR=f"1.2.3.{number}",
            )
        response = self.client.post(
            "/accounts/login/",
            {"email": "victim@example.com", "password": "wrong-password"},
            REMOTE_ADDR="10.0.0.1",
            HTTP_X_FORWARDED_FOR="9.9.9.9",
        )
        self.assertEqual(response.status_code, 429)


class SignupRateLimitTests(RealCacheMixin, TestCase):
    def signup(self, number, ip="10.0.0.1"):
        return self.client.post(
            "/accounts/signup/",
            {"email": f"user{number}@example.com", "password": "longenough1", "consent": "on"},
            REMOTE_ADDR=ip,
        )

    def test_ten_signups_per_hour_per_ip_then_429_and_no_account_created(self):
        for number in range(ratelimit.SIGNUP_MAX_POSTS_PER_IP):
            self.assertEqual(self.signup(number).status_code, 302)
        response = self.signup(99)
        self.assertEqual(response.status_code, 429)
        self.assertIn(ratelimit.SIGNUP_BLOCKED_MESSAGE, response.context["form"].non_field_errors())
        self.assertFalse(User.objects.filter(email="user99@example.com").exists())
        self.assertEqual(User.objects.count(), 10)

    def test_another_ip_is_not_affected(self):
        for number in range(11):
            self.signup(number)
        self.assertEqual(self.signup(500, ip="10.0.0.2").status_code, 302)

    def test_viewing_the_signup_page_is_not_counted(self):
        for _ in range(20):
            self.client.get("/accounts/signup/", REMOTE_ADDR="10.0.0.1")
        self.assertEqual(self.signup(1).status_code, 302)


class ClientIpTests(TestCase):
    def request(self, **meta):
        from django.test import RequestFactory

        return RequestFactory().get("/", **meta)

    def test_default_ignores_x_forwarded_for(self):
        request = self.request(REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR="6.6.6.6")
        self.assertEqual(ratelimit.client_ip(request), "10.0.0.1")

    @override_settings(NUM_PROXIES=1)
    def test_with_one_trusted_proxy_the_last_address_is_used(self):
        # Our proxy appended 5.5.5.5; the client typed "6.6.6.6" to try to fool us.
        request = self.request(REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR="6.6.6.6, 5.5.5.5")
        self.assertEqual(ratelimit.client_ip(request), "5.5.5.5")

    @override_settings(NUM_PROXIES=2)
    def test_with_more_proxies_than_addresses_the_first_address_is_used(self):
        request = self.request(REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR="5.5.5.5")
        self.assertEqual(ratelimit.client_ip(request), "5.5.5.5")

    @override_settings(NUM_PROXIES=1)
    def test_without_the_header_the_connecting_address_is_used(self):
        self.assertEqual(ratelimit.client_ip(self.request(REMOTE_ADDR="10.0.0.1")), "10.0.0.1")
