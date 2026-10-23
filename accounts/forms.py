from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone

from .models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "role")


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("email", "role", "is_active", "is_staff")


class SignupForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        min_length=8,
        label="Password",
    )
    consent = forms.BooleanField(
        required=True,
        label="I am 18 or older and agree to the Terms and Privacy Policy",
        error_messages={
            "required": "You must confirm that you are 18 or older and agree to the Terms "
            "and Privacy Policy to create an account.",
        },
    )

    class Meta:
        model = User
        fields = ("email", "password")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        if password:
            # Same rules as AUTH_PASSWORD_VALIDATORS in settings (length, common
            # passwords, all digits, too similar to the email).
            email = cleaned_data.get("email") or self.data.get("email", "").strip().lower()
            try:
                validate_password(password, user=User(email=email))
            except forms.ValidationError as error:
                self.add_error("password", error)
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.role = "ANALYST"
        user.consented_at = timezone.now()  # proof of consent (DPDP Act 2023)
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


class DeleteAccountForm(forms.Form):
    """Two checks before an account is erased: the password, and an explicit tick."""

    password = forms.CharField(widget=forms.PasswordInput, label="Your password")
    confirm = forms.BooleanField(
        label="I understand that this permanently deletes my account, datasets, rows and decisions",
        error_messages={"required": "Tick the box to confirm that you want to delete your account."},
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not self.user.check_password(password):
            raise forms.ValidationError("That password is not correct.", code="incorrect_password")
        return password
