"""Tests for audit S8 (headers part): Referrer-Policy and Content-Security-Policy."""
import re
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, TestCase

from bizmind.middleware import ContentSecurityPolicyMiddleware, build_csp_header
from bizmind.testing import make_dataset, make_user


def parse_csp(header):
    """'a x y; b z' -> {'a': ['x', 'y'], 'b': ['z']}"""
    return {
        part.split()[0]: part.split()[1:]
        for part in header.split(";")
        if part.strip()
    }


class HeaderBuilderTests(SimpleTestCase):
    def test_builds_the_header_text_from_a_dict(self):
        header = build_csp_header({"default-src": ["'self'"], "img-src": ["'self'", "data:"]})
        self.assertEqual(header, "default-src 'self'; img-src 'self' data:")

    def test_middleware_adds_the_header(self):
        middleware = ContentSecurityPolicyMiddleware(lambda request: HttpResponse("ok"))
        response = middleware(RequestFactory().get("/"))
        self.assertEqual(response["Content-Security-Policy"], build_csp_header())

    def test_middleware_does_not_overwrite_a_header_set_by_a_view(self):
        def view(request):
            response = HttpResponse("ok")
            response["Content-Security-Policy"] = "default-src 'none'"
            return response

        response = ContentSecurityPolicyMiddleware(view)(RequestFactory().get("/"))
        self.assertEqual(response["Content-Security-Policy"], "default-src 'none'")


class HeadersOnRealResponsesTests(TestCase):
    def setUp(self):
        self.user = make_user("analyst@example.com")
        self.dataset = make_dataset(self.user, name="D", is_processed=True)

    def urls(self):
        return {
            "home": "/",
            "login": "/accounts/login/",
            "dashboard": "/dashboard/",
            "dataset page": f"/datasets/{self.dataset.pk}/",
            "api json": "/api/datasets/",
            "swagger": "/api/docs/",
            "404 page": "/definitely-not-a-page/",
        }

    def test_every_kind_of_response_has_both_headers(self):
        self.client.force_login(self.user)
        for label, url in self.urls().items():
            with self.subTest(page=label):
                response = self.client.get(url)
                self.assertEqual(response.headers["Referrer-Policy"], "same-origin")
                self.assertIn("Content-Security-Policy", response.headers)

    def test_redirects_and_405_responses_are_covered_too(self):
        self.assertIn("Content-Security-Policy", self.client.get("/dashboard/").headers)  # 302
        self.client.force_login(self.user)
        self.assertIn("Content-Security-Policy", self.client.get("/accounts/logout/").headers)  # 405

    def test_the_older_security_headers_are_still_there(self):
        headers = self.client.get("/accounts/login/").headers
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(headers["X-Frame-Options"], "DENY")


class PolicyContentTests(SimpleTestCase):
    def setUp(self):
        self.policy = parse_csp(build_csp_header())

    def test_the_dangerous_directives_are_locked_down(self):
        self.assertEqual(self.policy["default-src"], ["'self'"])
        self.assertEqual(self.policy["object-src"], ["'none'"])
        self.assertEqual(self.policy["base-uri"], ["'self'"])
        self.assertEqual(self.policy["form-action"], ["'self'"])
        self.assertEqual(self.policy["frame-ancestors"], ["'none'"])
        self.assertEqual(self.policy["connect-src"], ["'self'"])

    def test_scripts_cannot_use_eval_or_arbitrary_hosts(self):
        scripts = self.policy["script-src"]
        self.assertNotIn("'unsafe-eval'", scripts)
        self.assertNotIn("*", scripts)
        self.assertNotIn("http:", scripts)
        self.assertNotIn("https:", scripts)

    def test_every_external_host_used_by_a_template_is_allowed(self):
        """Adding a CDN to a template without updating the policy must fail here.

        <script src> hosts are checked against script-src and
        <link href> (stylesheet) hosts against style-src.
        """
        script_hosts, style_hosts = set(), set()
        for path in Path(settings.BASE_DIR, "templates").rglob("*.html"):
            html = path.read_text(encoding="utf-8")
            script_hosts.update(re.findall(r'<script[^>]*\bsrc="(https://[^/"]+)', html))
            style_hosts.update(re.findall(r'<link[^>]*\bhref="(https://[^/"]+)', html))

        self.assertTrue(script_hosts and style_hosts, "expected the current templates to use CDN hosts")
        self.assertLessEqual(script_hosts, set(self.policy["script-src"]))
        self.assertLessEqual(style_hosts, set(self.policy["style-src"]))
