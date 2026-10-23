"""Rate-limited wrapper around the Django admin login (audit SEC-1).

Django's own admin login has no brute-force protection. This view sits in
front of it (see bizmind/urls.py): it counts failed POSTs per IP address and per
username and answers 429 once either is over its limit, then hands the request
to the normal admin login. Only staff accounts can ever log in there; that rule
is Django's AdminSite.has_permission (is_active and is_staff).
"""
from django.contrib import admin
from django.http import HttpResponse

from . import ratelimit

ADMIN_LOGIN_BLOCKED_MESSAGE = "Too many failed login attempts. Please wait 15 minutes and try again."


def rate_limited_admin_login(request, *args, **kwargs):
    is_post = request.method == "POST"
    username = request.POST.get("username", "") if is_post else ""

    if is_post and ratelimit.admin_login_is_blocked(request, username):
        response = HttpResponse(ADMIN_LOGIN_BLOCKED_MESSAGE, status=429, content_type="text/plain")
        response["Retry-After"] = str(ratelimit.ADMIN_LOGIN_WINDOW_SECONDS)
        return response

    response = admin.site.login(request, *args, **kwargs)

    if is_post:
        if response.status_code == 200:  # the form was shown again: wrong login
            ratelimit.record_admin_login_failure(request, username)
        elif response.status_code in (301, 302):  # logged in
            ratelimit.reset_admin_login_failures(request, username)
    return response
