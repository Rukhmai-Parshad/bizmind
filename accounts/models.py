from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)

    # Data minimisation: BizMind never asks for a name and does not record login
    # times, so these inherited columns are removed instead of left empty.
    first_name = None
    last_name = None
    last_login = None

    # When the person ticked "I am 18 or older and agree to the Terms and Privacy
    # Policy" at signup. Null for accounts created before consent was recorded
    # (and for accounts created in the admin or with createsuperuser).
    consented_at = models.DateTimeField(null=True, blank=True)

    ROLE_CHOICES = (
        ("ADMIN", "Admin"),
        ("ANALYST", "Analyst"),
        ("VIEWER", "Viewer"),
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default="VIEWER",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def is_admin(self):
        return self.role == "ADMIN"

    def is_analyst(self):
        return self.role == "ANALYST"

    def is_viewer(self):
        return self.role == "VIEWER"

    def __str__(self):
        return self.email
