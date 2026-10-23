"""Rate limiting for the web login and signup forms (audit S4).

Counters live in Django's cache. They use a fixed time window: the window
starts at the first hit and the counter disappears when it ends.

Login counts FAILED attempts under three keys, and blocks when ANY of them
is over its limit:
  * this email from this IP   (stops guessing one account)
  * this IP, any email        (stops one machine trying many accounts)
  * this email, any IP        (stops guessing one account from many machines)
Using the (email + IP) key first means a stranger cannot easily lock YOU out
of your own account: they would need many failures from many addresses.
"""
import hashlib

from django.conf import settings
from django.core.cache import cache

LOGIN_WINDOW_SECONDS = 15 * 60
LOGIN_MAX_FAILURES_PER_EMAIL_AND_IP = 5
LOGIN_MAX_FAILURES_PER_IP = 20
LOGIN_MAX_FAILURES_PER_EMAIL = 20

SIGNUP_WINDOW_SECONDS = 60 * 60
SIGNUP_MAX_POSTS_PER_IP = 10

ADMIN_LOGIN_WINDOW_SECONDS = 15 * 60
ADMIN_LOGIN_MAX_FAILURES_PER_IP = 10
ADMIN_LOGIN_MAX_FAILURES_PER_USERNAME = 10

LOGIN_BLOCKED_MESSAGE = "Too many failed login attempts. Please wait 15 minutes and try again."
SIGNUP_BLOCKED_MESSAGE = "Too many sign-up attempts from this address. Please try again later."


def client_ip(request):
    """The caller's IP address.

    X-Forwarded-For is client-controlled, so it is ignored unless
    settings.NUM_PROXIES says how many trusted proxies sit in front of the
    app. With NUM_PROXIES=1 we take the LAST address in the header, i.e. the
    one our own proxy appended (anything the client typed is further left).
    """
    remote_addr = request.META.get("REMOTE_ADDR", "")
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    proxies = getattr(settings, "NUM_PROXIES", 0)

    if proxies <= 0 or not forwarded:
        return remote_addr

    addresses = [part.strip() for part in forwarded.split(",") if part.strip()]
    if not addresses:
        return remote_addr
    return addresses[-min(proxies, len(addresses))]


def _key(*parts):
    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()
    return f"ratelimit:{digest}"


def _hit(key, window):
    """Add 1 to the counter (creating it with the window if new)."""
    if cache.add(key, 1, window):
        return 1
    try:
        return cache.incr(key)
    except ValueError:  # expired between add() and incr()
        cache.set(key, 1, window)
        return 1


def _login_keys(request, email):
    ip = client_ip(request)
    email = email.strip().lower()
    return (
        (_key("login", ip, email), LOGIN_MAX_FAILURES_PER_EMAIL_AND_IP),
        (_key("login-ip", ip), LOGIN_MAX_FAILURES_PER_IP),
        (_key("login-email", email), LOGIN_MAX_FAILURES_PER_EMAIL),
    )


def login_is_blocked(request, email):
    return any(cache.get(key, 0) >= limit for key, limit in _login_keys(request, email))


def record_login_failure(request, email):
    for key, _limit in _login_keys(request, email):
        _hit(key, LOGIN_WINDOW_SECONDS)


def reset_login_failures(request, email):
    """After a successful login forget the (email + IP) failures only."""
    cache.delete(_login_keys(request, email)[0][0])


def signup_is_blocked(request):
    """Count this signup POST and say whether the IP is now over its limit."""
    return _hit(_key("signup", client_ip(request)), SIGNUP_WINDOW_SECONDS) > SIGNUP_MAX_POSTS_PER_IP


def _admin_login_keys(request, username):
    return (
        (_key("admin-login-ip", client_ip(request)), ADMIN_LOGIN_MAX_FAILURES_PER_IP),
        (_key("admin-login-user", username.strip().lower()), ADMIN_LOGIN_MAX_FAILURES_PER_USERNAME),
    )


def admin_login_is_blocked(request, username):
    return any(cache.get(key, 0) >= limit for key, limit in _admin_login_keys(request, username))


def record_admin_login_failure(request, username):
    for key, _limit in _admin_login_keys(request, username):
        _hit(key, ADMIN_LOGIN_WINDOW_SECONDS)


def reset_admin_login_failures(request, username):
    """After a successful admin login forget the failures for that account only."""
    cache.delete(_admin_login_keys(request, username)[1][0])
