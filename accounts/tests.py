from django.test import TestCase
from django.urls import reverse

from .models import User

PASSWORD = "strong-password-123"


class UserModelTests(TestCase):
    def test_user_uses_email_for_login(self):
        user = User.objects.create_user(
            email="user@example.com",
            password=PASSWORD,
        )

        self.assertEqual(user.email, "user@example.com")
        self.assertFalse(user.is_staff)
        self.assertTrue(user.check_password(PASSWORD))
        self.assertEqual(user.role, "VIEWER")


class LoginCharacterisationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="analyst@example.com",
            password=PASSWORD,
            role="ANALYST",
        )
        self.login_url = reverse("accounts:login")

    def test_login_page_renders(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)

    def test_valid_login_redirects_to_dashboard(self):
        response = self.client.post(
            self.login_url,
            {"email": "analyst@example.com", "password": PASSWORD},
        )
        self.assertRedirects(response, reverse("dashboard:home"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_invalid_login_stays_on_page(self):
        response = self.client.post(
            self.login_url,
            {"email": "analyst@example.com", "password": "wrong-password"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertContains(response, "Invalid email or password.")

    def test_authenticated_user_is_sent_to_dashboard(self):
        self.client.force_login(self.user)
        response = self.client.get(self.login_url)
        self.assertRedirects(response, reverse("dashboard:home"))
