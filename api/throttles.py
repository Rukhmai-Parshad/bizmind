"""Throttles for the JWT token endpoints (audit S4).

Rates are set in settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].
Both count every request (not only failures) inside the time window.
"""
from rest_framework.throttling import SimpleRateThrottle


class AuthIPRateThrottle(SimpleRateThrottle):
    """Limits how often one IP address may call the token endpoints."""

    scope = "auth_ip"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class AuthAccountRateThrottle(SimpleRateThrottle):
    """Limits attempts against ONE account (the email in the request body).

    This is what slows down password guessing even if the guesser rotates IPs.
    """

    scope = "auth_account"

    def get_cache_key(self, request, view):
        email = ""
        if hasattr(request.data, "get"):
            email = str(request.data.get("email") or "").strip().lower()
        ident = email or self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}
