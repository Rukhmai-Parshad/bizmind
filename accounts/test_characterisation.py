"""Characterisation tests: how signup, login and logout behave today."""
from django.test import TestCase

from accounts.models import User
from bizmind.testing import PASSWORD, make_user, message_texts


class LoginTests(TestCase):
    def setUp(self):
        self.user = make_user("analyst@example.com")

    def test_valid_login_redirects_to_dashboard(self):
        response = self.client.post(
            "/accounts/login/",
            {"email": "analyst@example.com", "password": PASSWORD},
        )
        self.assertRedirects(response, "/dashboard/", fetch_redirect_response=False)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_wrong_password_shows_generic_error_and_stays_logged_out(self):
        response = self.client.post(
            "/accounts/login/",
            {"email": "analyst@example.com", "password": "wrong-password"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Invalid email or password.", response.context["form"].non_field_errors()
        )
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_unknown_email_gets_the_same_generic_error(self):
        response = self.client.post(
            "/accounts/login/",
            {"email": "nobody@example.com", "password": PASSWORD},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Invalid email or password.", response.context["form"].non_field_errors()
        )

    def test_logged_in_user_visiting_login_is_sent_to_dashboard(self):
        self.client.force_login(self.user)
        response = self.client.get("/accounts/login/")
        self.assertRedirects(response, "/dashboard/", fetch_redirect_response=False)

    def test_dashboard_requires_login(self):
        response = self.client.get("/dashboard/")
        self.assertRedirects(
            response,
            "/accounts/login/?next=/dashboard/",
            fetch_redirect_response=False,
        )

    def test_login_email_is_case_sensitive_today(self):
        # Signup lower-cases the email but login does not, so an upper-case
        # email typed at login does not match a stored lower-case email.
        response = self.client.post(
            "/accounts/login/",
            {"email": "ANALYST@EXAMPLE.COM", "password": PASSWORD},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)


class SignupTests(TestCase):
    def test_signup_creates_an_analyst_and_redirects_to_login(self):
        response = self.client.post(
            "/accounts/signup/",
            {"email": "New@Example.com", "password": "longenough1"},
        )
        self.assertRedirects(response, "/accounts/login/", fetch_redirect_response=False)
        self.assertIn(
            "Account created successfully. Please log in.", message_texts(response)
        )
        user = User.objects.get(email="new@example.com")  # stored lower-case
        self.assertEqual(user.role, "ANALYST")
        self.assertTrue(user.check_password("longenough1"))

    def test_role_sent_by_the_client_is_ignored(self):
        self.client.post(
            "/accounts/signup/",
            {"email": "sneaky@example.com", "password": "longenough1", "role": "ADMIN"},
        )
        user = User.objects.get(email="sneaky@example.com")
        self.assertEqual(user.role, "ANALYST")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_duplicate_email_is_rejected_ignoring_case(self):
        make_user("taken@example.com")
        response = self.client.post(
            "/accounts/signup/",
            {"email": "TAKEN@example.com", "password": "longenough1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "An account with this email already exists.",
            response.context["form"].errors["email"],
        )
        self.assertEqual(User.objects.count(), 1)

    def test_password_shorter_than_8_characters_is_rejected(self):
        response = self.client.post(
            "/accounts/signup/",
            {"email": "short@example.com", "password": "short"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("password", response.context["form"].errors)
        self.assertFalse(User.objects.filter(email="short@example.com").exists())

    def test_django_password_validators_are_not_applied_today(self):
        # docs/03_App_Flow.md says "min 8 plus Django validators", but the form
        # only checks length. A very common, all-numeric password is accepted.
        response = self.client.post(
            "/accounts/signup/",
            {"email": "weak@example.com", "password": "12345678"},
        )
        self.assertRedirects(response, "/accounts/login/", fetch_redirect_response=False)
        self.assertTrue(User.objects.filter(email="weak@example.com").exists())


class LogoutTests(TestCase):
    def test_logout_with_get_does_not_log_the_user_out(self):
        # Audit S3 (fixed in Milestone 1): logout is POST-only. See test_security.py.
        self.client.force_login(make_user())
        response = self.client.get("/accounts/logout/")
        self.assertEqual(response.status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)

    def test_logout_with_post_also_works(self):
        self.client.force_login(make_user())
        response = self.client.post("/accounts/logout/")
        self.assertRedirects(response, "/accounts/login/", fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", self.client.session)
