from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from . import ratelimit
from .forms import LoginForm, SignupForm


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
