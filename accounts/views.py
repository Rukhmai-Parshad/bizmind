from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from . import ratelimit
from decisions.models import Decision

from .forms import DeleteAccountForm, LoginForm, SignupForm
from .services import delete_account as erase_account


def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    if request.method == "POST":
        if ratelimit.signup_is_blocked(request):
            form = SignupForm(request.POST)
            form.full_clean()  # add_error() needs a validated form
            form.add_error(None, ratelimit.SIGNUP_BLOCKED_MESSAGE)
            return render(request, "accounts/signup.html", {"form": form}, status=429)

        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully. Please log in.")
            return redirect("accounts:login")
    else:
        form = SignupForm()

    return render(request, "accounts/signup.html", {"form": form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]

            if ratelimit.login_is_blocked(request, email):
                form.add_error(None, ratelimit.LOGIN_BLOCKED_MESSAGE)
                return render(request, "accounts/login.html", {"form": form}, status=429)

            user = authenticate(
                request,
                email=email,
                password=form.cleaned_data["password"],
            )
            if user is not None:
                ratelimit.reset_login_failures(request, email)
                login(request, user)
                return redirect("dashboard:home")

            ratelimit.record_login_failure(request, email)
            form.add_error(None, "Invalid email or password.")
    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})


@require_POST  # a GET link could be triggered by another website (audit S3)
def user_logout(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("accounts:login")


@login_required
def account_settings(request):
    user = request.user
    return render(
        request,
        "accounts/settings.html",
        {
            "dataset_count": user.datasets.count(),
            "decision_count": Decision.objects.filter(dataset__uploaded_by=user).count(),
            "can_delete": not (user.is_staff or user.is_superuser),
        },
    )


@login_required
def delete_account(request):
    """Confirmation page (GET) and erasure (POST). Needs the password and a tick."""
    user = request.user

    if user.is_staff or user.is_superuser:
        messages.error(
            request,
            "Staff accounts cannot be deleted here. Ask another administrator to remove it in the admin site.",
        )
        return redirect("accounts:settings")

    if request.method == "POST":
        form = DeleteAccountForm(user, request.POST)

        if ratelimit.login_is_blocked(request, user.email):
            form.full_clean()
            form.add_error(None, ratelimit.LOGIN_BLOCKED_MESSAGE)
            return render(request, "accounts/delete_account.html", {"form": form}, status=429)

        if form.is_valid():
            erase_account(user)
            logout(request)
            messages.success(request, "Your account and all its data have been deleted.")
            return redirect("core:home")

        if form.has_error("password", code="incorrect_password"):
            ratelimit.record_login_failure(request, user.email)
    else:
        form = DeleteAccountForm(user)

    return render(request, "accounts/delete_account.html", {"form": form})
