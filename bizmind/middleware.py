"""Content-Security-Policy header (audit S8).

Django 5.2 has no built-in CSP, so this tiny middleware adds the header.
The policy itself is the CONTENT_SECURITY_POLICY dict in settings.py.
"""
from django.conf import settings


def build_csp_header(policy=None):
    """Turn {"script-src": ["'self'", ...], ...} into the header text."""
    policy = settings.CONTENT_SECURITY_POLICY if policy is None else policy
    return "; ".join(
        f"{directive} {' '.join(sources)}" for directive, sources in policy.items()
    )


class ContentSecurityPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # A view that sets its own CSP wins; everything else gets the default.
        if "Content-Security-Policy" not in response:
            response["Content-Security-Policy"] = build_csp_header()
        return response
