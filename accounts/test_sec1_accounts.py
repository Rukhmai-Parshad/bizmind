"""SEC-1 tests: password validators on signup and the protected admin login."""
from django.conf import global_settings
from unittest import skipIf

from django.conf import settings
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from accounts import ratelimit
from accounts.models import User
from bizmind.testing import PASSWORD, RealCacheMixin, make_user


def signup(client, email, password):
    return client.post(
        "/accounts/signup/",
        {"email": email, "password": password, "consent": "on"},
    )


class SignupPasswordValidatorTests(TestCase):
    def assert_rejected(self, email, password):
        response = signup(self.client, email, password)
        self.assertEqual(response.status_code, 200)
        self.assertIn("password", response.context["form"].errors)
        self.assertFalse(User.objects.filter(email=email).exists())

    def test_all_numeric_password_is_rejected(self):
        self.assert_rejected("a@example.com", "48291746")

    def test_common_password_is_rejected(self):
        self.assert_rejected("b@example.com", "password")

    def test_password_too_similar_to_the_email_is_rejected(self):
        self.assert_rejected("rukhmai@example.com", "rukhmai12")

    def test_short_password_is_still_rejected(self):
        self.assert_rejected("c@example.com", "Ab1!x")

    def test_error_text_is_shown_on_the_page(self):
        response = signup(self.client, "d@example.com", "12345678")
        self.assertContains(response, "field-error")

    def test_a_strong_password_still_signs_up(self):
        response = signup(self.client, "e@example.com", PASSWORD)
        self.assertRedirects(response, "/accounts/login/", fetch_redirect_response=False)
        self.assertTrue(User.objects.filter(email="e@example.com").exists())

    def test_rate_limited_signup_page_still_renders(self):
        # The 429 path builds the form and validates it too.
        with self.settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}):
            from django.core.cache import cache
            cache.clear()
            for _ in range(ratelimit.SIGNUP_MAX_POSTS_PER_IP):
                signup(self.client, "f@example.com", "12345678")
            response = signup(self.client, "f@example.com", "12345678")
            self.assertEqual(response.status_code, 429)
            cache.clear()


class PasswordHashingTests(SimpleTestCase):
    def test_settings_use_a_strong_hasher_first(self):
        # The test runner swaps in a fast MD5 hasher, so read the settings FILE's
        # value (falling back to Django's default list when it sets none).
        from bizmind import settings as project_settings

        hashers = getattr(project_settings, "PASSWORD_HASHERS", global_settings.PASSWORD_HASHERS)
        self.assertEqual(hashers[0], "django.contrib.auth.hashers.PBKDF2PasswordHasher")
        weak = {
            "django.contrib.auth.hashers." + name
            for name in (
                "MD5PasswordHasher",
                "SHA1PasswordHasher",
                "UnsaltedMD5PasswordHasher",
                "UnsaltedSHA1PasswordHasher",
                "CryptPasswordHasher",
            )
        }
        self.assertFalse(weak.intersection(hashers))


class NoDefaultAccountsTests(TestCase):
    def test_a_fresh_database_has_no_users(self):
        # No migration or fixture creates an account, so there is no default login.
        self.assertEqual(User.objects.count(), 0)


class AdminLocationTests(TestCase):
    @skipIf(settings.ADMIN_URL == "admin/", "ADMIN_URL is deliberately set back to admin/")
    def test_old_admin_path_is_gone(self):
        self.assertEqual(self.client.get("/admin/").status_code, 404)
        self.assertEqual(self.client.get("/admin/login/").status_code, 404)

    def test_admin_lives_at_the_configured_path(self):
        self.assertEqual(reverse("admin:login"), f"/{settings.ADMIN_URL}login/")
        self.assertEqual(self.client.get(reverse("admin:login")).status_code, 200)

    def test_anonymous_visitor_is_sent_to_the_admin_login(self):
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response["Location"])


class AdminStaffOnlyTests(TestCase):
    def login(self, email, password=PASSWORD):
        return self.client.post(reverse("admin:login"), {"username": email, "password": password})

    def test_a_normal_user_with_the_right_password_cannot_enter(self):
        make_user("analyst@example.com", role="ANALYST")
        response = self.login("analyst@example.com")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_an_admin_role_without_staff_flag_cannot_enter(self):
        make_user("role-admin@example.com", role="ADMIN")
        self.login("role-admin@example.com")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_a_logged_in_normal_user_is_bounced_from_the_admin(self):
        self.client.force_login(make_user("analyst@example.com"))
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response["Location"])

    def test_a_staff_user_can_enter(self):
        User.objects.create_superuser(email="root@example.com", password=PASSWORD)
        self.assertEqual(self.login("root@example.com").status_code, 302)
        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 200)


class AdminLoginRateLimitTests(RealCacheMixin, TestCase):
    def setUp(self):
        super().setUp()
        User.objects.create_superuser(email="root@example.com", password=PASSWORD)

    def attempt(self, username="root@example.com", password="wrong", ip="10.0.0.1"):
        return self.client.post(
            reverse("admin:login"),
            {"username": username, "password": password},
            REMOTE_ADDR=ip,
        )

    def test_wrong_passwords_are_blocked_after_the_limit(self):
        for _ in range(ratelimit.ADMIN_LOGIN_MAX_FAILURES_PER_IP):
            self.assertEqual(self.attempt().status_code, 200)
        response = self.attempt()
        self.assertEqual(response.status_code, 429)
        self.assertIn("Retry-After", response)

    def test_the_right_password_is_refused_while_blocked(self):
        for _ in range(ratelimit.ADMIN_LOGIN_MAX_FAILURES_PER_IP):
            self.attempt()
        self.assertEqual(self.attempt(password=PASSWORD).status_code, 429)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_one_account_is_protected_even_when_the_ip_changes(self):
        for number in range(ratelimit.ADMIN_LOGIN_MAX_FAILURES_PER_USERNAME):
            self.attempt(ip=f"10.0.1.{number}")
        self.assertEqual(self.attempt(ip="10.0.9.9").status_code, 429)

    def test_one_ip_is_blocked_even_when_the_username_changes(self):
        for number in range(ratelimit.ADMIN_LOGIN_MAX_FAILURES_PER_IP):
            self.attempt(username=f"user{number}@example.com")
        self.assertEqual(self.attempt(username="other@example.com").status_code, 429)

    def test_another_ip_and_account_are_not_affected(self):
        for _ in range(ratelimit.ADMIN_LOGIN_MAX_FAILURES_PER_IP):
            self.attempt()
        self.assertEqual(self.attempt(username="someone@example.com", ip="10.0.5.5").status_code, 200)

    def test_a_successful_login_forgets_that_accounts_failures(self):
        limit = ratelimit.ADMIN_LOGIN_MAX_FAILURES_PER_USERNAME
        for number in range(limit - 1):  # one failure short of the limit
            self.attempt(ip=f"10.0.1.{number}")
        self.assertEqual(self.attempt(password=PASSWORD, ip="10.0.2.1").status_code, 302)
        self.client.logout()
        # Counted from zero again: another limit-1 failures do not block. Without
        # the reset the account would already be blocked here.
        for number in range(limit - 1):
            self.assertEqual(self.attempt(ip=f"10.0.3.{number}").status_code, 200)
        self.assertEqual(self.attempt(password=PASSWORD, ip="10.0.4.1").status_code, 302)

    def test_viewing_the_login_page_is_never_blocked(self):
        for _ in range(ratelimit.ADMIN_LOGIN_MAX_FAILURES_PER_IP + 1):
            self.attempt()
        self.assertEqual(self.client.get(reverse("admin:login"), REMOTE_ADDR="10.0.0.1").status_code, 200)
