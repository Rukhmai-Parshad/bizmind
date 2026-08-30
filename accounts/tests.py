from django.test import TestCase

from .models import User


class UserModelTests(TestCase):
    def test_user_uses_email_for_login(self):
        user = User.objects.create_user(
            email="user@example.com",
            password="strong-password-123",
        )

        self.assertEqual(user.email, "user@example.com")
        self.assertFalse(user.is_staff)
        self.assertTrue(user.check_password("strong-password-123"))
