"""Tests for audit S3: logout must be POST-only (and CSRF protected)."""
import re

from django.test import Client, TestCase

from bizmind.testing import make_user, message_texts


class LogoutIsPostOnlyTests(TestCase):
    def setUp(self):
        self.user = make_user("analyst@example.com")
        self.client.force_login(self.user)

    def test_get_returns_405_and_the_user_stays_logged_in(self):
        response = self.client.get("/accounts/logout/")
        self.assertEqual(response.status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)
        # Still logged in: the dashboard opens instead of redirecting to login.
        self.assertEqual(self.client.get("/dashboard/").status_code, 200)

    def test_other_methods_are_also_refused(self):
        for method in ("put", "patch", "delete"):
            with self.subTest(method=method):
                response = getattr(self.client, method)("/accounts/logout/")
                self.assertEqual(response.status_code, 405)
                self.assertIn("_auth_user_id", self.client.session)

    def test_post_logs_out_and_shows_the_message(self):
        response = self.client.post("/accounts/logout/")
        self.assertRedirects(response, "/accounts/login/", fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertIn("You have been logged out.", message_texts(response))

    def test_post_without_a_csrf_token_is_refused(self):
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.user)
        response = strict.post("/accounts/logout/")
        self.assertEqual(response.status_code, 403)
        self.assertIn("_auth_user_id", strict.session)

    def test_post_with_the_csrf_token_from_the_page_works(self):
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.user)
        page = strict.get("/dashboard/").content.decode()
        token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', page).group(1)
        response = strict.post("/accounts/logout/", {"csrfmiddlewaretoken": token})
        self.assertRedirects(response, "/accounts/login/", fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", strict.session)


class LogoutButtonsAreFormsTests(TestCase):
    """The nav must not contain a plain logout link any more, only a POST form."""

    def setUp(self):
        self.client.force_login(make_user("analyst@example.com"))

    def assert_logout_is_a_post_form(self, url):
        html = self.client.get(url).content.decode()
        self.assertNotIn('href="/accounts/logout/"', html)
        form = re.search(r'<form[^>]*action="/accounts/logout/"[^>]*>(.*?)</form>', html, re.S)
        self.assertIsNotNone(form, f"no logout form on {url}")
        self.assertIn('method="post"', form.group(0))
        self.assertIn("csrfmiddlewaretoken", form.group(1))
        self.assertIn("Logout", form.group(1))

    def test_dashboard_navbar_logout_is_a_post_form(self):
        self.assert_logout_is_a_post_form("/dashboard/")

    def test_public_navbar_logout_is_a_post_form_when_logged_in(self):
        self.assert_logout_is_a_post_form("/")
