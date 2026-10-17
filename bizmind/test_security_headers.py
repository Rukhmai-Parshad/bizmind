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
    """Milestone 3: everything is self-hosted, so the policy allows 'self' only."""

    ALLOWED_SOURCES = {"'self'", "'none'", "data:"}

    def setUp(self):
        self.policy = parse_csp(build_csp_header())

    def test_the_dangerous_directives_are_locked_down(self):
        self.assertEqual(self.policy["default-src"], ["'self'"])
        self.assertEqual(self.policy["object-src"], ["'none'"])
        self.assertEqual(self.policy["base-uri"], ["'self'"])
        self.assertEqual(self.policy["form-action"], ["'self'"])
        self.assertEqual(self.policy["frame-ancestors"], ["'none'"])
        self.assertEqual(self.policy["connect-src"], ["'self'"])

    def test_scripts_and_styles_are_self_only(self):
        self.assertEqual(self.policy["script-src"], ["'self'"])
        self.assertEqual(self.policy["style-src"], ["'self'"])
        self.assertEqual(self.policy["font-src"], ["'self'"])

    def test_no_external_host_unsafe_inline_or_unsafe_eval_anywhere(self):
        for directive, sources in self.policy.items():
            with self.subTest(directive=directive):
                self.assertLessEqual(set(sources), self.ALLOWED_SOURCES)

    def test_only_images_may_use_data_uris(self):
        for directive, sources in self.policy.items():
            if directive != "img-src":
                with self.subTest(directive=directive):
                    self.assertNotIn("data:", sources)


class TemplatesMatchThePolicyTests(SimpleTestCase):
    """The templates and static files must not need anything the policy forbids."""

    def files(self, folder, pattern):
        return list(Path(settings.BASE_DIR, folder).rglob(pattern))

    def test_no_template_loads_anything_from_another_host(self):
        loads = re.compile(r'\b(?:src|href|action)\s*=\s*"(?:https?:)?//', re.I)
        for path in self.files("templates", "*.html"):
            with self.subTest(template=path.name):
                self.assertIsNone(loads.search(path.read_text(encoding="utf-8")))

    def test_no_template_has_inline_script_style_or_event_handlers(self):
        inline_script = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>", re.I)
        patterns = {
            "inline <script>": inline_script,
            "<style> block": re.compile(r"<style\b", re.I),
            'style="" attribute': re.compile(r'\sstyle\s*=', re.I),
            "on...= handler": re.compile(r'\son[a-z]+\s*=', re.I),
            "javascript: url": re.compile(r"javascript:", re.I),
        }
        for path in self.files("templates", "*.html"):
            html = path.read_text(encoding="utf-8")
            for label, pattern in patterns.items():
                with self.subTest(template=path.name, found=label):
                    self.assertIsNone(pattern.search(html))

    def test_css_and_js_load_nothing_external(self):
        for path in self.files("static", "*.css") + self.files("static", "*.js"):
            text = path.read_text(encoding="utf-8")
            with self.subTest(file=path.name):
                self.assertNotRegex(text, r"@import|url\(\s*['\"]?(?:https?:)?//")

    def test_removed_third_party_assets_are_really_gone(self):
        for forbidden in ("unpkg", "cdnjs", "jsdelivr", "googleapis", "font-awesome", "aos.js", "chart.js"):
            for path in self.files("templates", "*.html"):
                with self.subTest(template=path.name, word=forbidden):
                    self.assertNotIn(forbidden, path.read_text(encoding="utf-8").lower())
        self.assertFalse(Path(settings.BASE_DIR, "static/img/about.jpg").exists())
        self.assertFalse(Path(settings.BASE_DIR, "static/css/style.css").exists())
        self.assertFalse(Path(settings.BASE_DIR, "static/dashboard/main.css").exists())

    def test_there_is_exactly_one_stylesheet(self):
        self.assertEqual([p.name for p in self.files("static", "*.css")], ["app.css"])
