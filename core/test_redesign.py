"""Tests for the warm redesign: new pages, favicon, and the design rules as guards."""
import re
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase, TestCase

from bizmind.testing import make_dataset, make_user

ROOT = Path(settings.BASE_DIR)
TEMPLATES = sorted((ROOT / "templates").rglob("*.html"))
STYLE = ROOT / "static/css/app.css"
SCRIPT = ROOT / "static/js/app.js"
DOC = ROOT / "docs/04_UI_UX_Design_Brief.md"
FILES_UNDER_RULES = TEMPLATES + [STYLE, SCRIPT] + ([DOC] if DOC.exists() else [])


class NewPagesTests(TestCase):
    def test_privacy_and_terms_load_for_visitors_and_users(self):
        for url in ("/privacy/", "/terms/"):
            with self.subTest(url=url, who="visitor"):
                self.assertEqual(self.client.get(url).status_code, 200)
        self.client.force_login(make_user())
        for url in ("/privacy/", "/terms/"):
            with self.subTest(url=url, who="user"):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_legal_pages_use_placeholders_and_a_fixed_date(self):
        for url in ("/privacy/", "/terms/"):
            html = self.client.get(url).content.decode()
            with self.subTest(url=url):
                self.assertIn("[OWNER NAME]", html)
                self.assertIn("[CONTACT EMAIL]", html)
                self.assertIn("Last updated: 18 October 2026", html)

    def test_privacy_page_states_what_the_code_really_does(self):
        html = self.client.get("/privacy/").content.decode().lower()
        for fact in ("deleted once processing has finished", "salted hash", "administration interface",
                     "session cookie", "csrf cookie", "messages cookie", "no analytics cookies",
                     "deleting an account also deletes its datasets"):
            with self.subTest(fact=fact):
                self.assertIn(fact, html)

    def test_terms_cover_advice_and_governing_law(self):
        html = self.client.get("/terms/").content.decode()
        self.assertIn("not financial, legal, tax or investment advice", html)
        self.assertIn("laws of India", html)

    def test_privacy_and_terms_are_linked_from_footers_and_signup(self):
        self.assertIn('href="/privacy/"', self.client.get("/").content.decode())
        self.assertIn('href="/terms/"', self.client.get("/").content.decode())
        signup = self.client.get("/accounts/signup/").content.decode()
        self.assertIn("By signing up you agree to the", signup)
        self.assertIn('href="/privacy/"', signup)
        self.assertIn('href="/terms/"', signup)
        self.client.force_login(make_user())
        app_page = self.client.get("/dashboard/").content.decode()
        self.assertIn('href="/privacy/"', app_page)
        self.assertIn('href="/terms/"', app_page)

    def test_messages_cookie_exists_as_the_privacy_page_says(self):
        self.client.force_login(make_user())
        response = self.client.post("/accounts/logout/")
        self.assertIn("messages", response.cookies)


class FaviconTests(TestCase):
    def test_favicon_ico_returns_the_svg_with_200(self):
        response = self.client.get("/favicon.ico")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/svg+xml")
        body = b"".join(response.streaming_content).decode()
        self.assertIn("#611E2F", body)
        self.assertIn("#E9E2D7", body)

    def test_pages_link_the_svg_favicon(self):
        for url in ("/", "/accounts/login/", "/nope/"):
            with self.subTest(url=url):
                self.assertIn('rel="icon" type="image/svg+xml" href="/static/img/favicon.svg"', self.client.get(url).content.decode())

    def test_500_page_links_the_favicon_too(self):
        from django.template.loader import render_to_string
        self.assertIn('href="/static/img/favicon.svg"', render_to_string("500.html"))


class LandingTests(TestCase):
    def test_landing_sections_exist(self):
        html = self.client.get("/").content.decode()
        for text in ("Decision intelligence for small business", "Works with your CSV", "How it works",
                     "Features", "Anatomy of a decision", "Example data", "See how it works",
                     "Explained decisions", "Confidence score", "Private by default",
                     "Sales, marketing and finance rules", "Secure REST API", "Sample files to try"):
            with self.subTest(text=text):
                self.assertIn(text, html)

    def test_landing_mockup_uses_values_from_the_sample_files(self):
        html = self.client.get("/").content.decode()
        for value in ("1.78%", "0.91", "0.11", "72.06%", "0.72"):
            self.assertIn(value, html)

    def test_logged_in_visitor_sees_app_links_in_the_top_bar(self):
        self.client.force_login(make_user("a@example.com", "ANALYST"))
        html = self.client.get("/").content.decode()
        self.assertIn("Go to dashboard", html)


class AppShellTests(TestCase):
    def setUp(self):
        self.user = make_user("analyst@example.com", "ANALYST")
        self.client.force_login(self.user)

    def test_sidebar_has_email_role_and_a_post_logout(self):
        html = self.client.get("/dashboard/").content.decode()
        self.assertIn("analyst@example.com", html)
        self.assertIn(">Analyst<", html)
        self.assertRegex(html, r'<form method="post" action="/accounts/logout/"')

    def test_search_field_and_slash_hint_exist_on_app_pages(self):
        html = self.client.get("/datasets/").content.decode()
        self.assertIn('id="page-search"', html)
        self.assertIn("<kbd", html)

    def test_upload_button_in_top_bar_is_hidden_for_viewers_and_on_the_upload_page(self):
        self.assertIn("Upload CSV", self.client.get("/dashboard/").content.decode())
        self.assertNotIn("Upload CSV", self.client.get("/datasets/upload/").content.decode())
        self.client.force_login(make_user("v@example.com", "VIEWER"))
        self.assertNotIn("Upload CSV", self.client.get("/dashboard/").content.decode())

    def test_breadcrumbs_on_detail_pages(self):
        dataset = make_dataset(self.user, "Q1 Sales", is_processed=True)
        html = self.client.get(f"/datasets/{dataset.pk}/").content.decode()
        self.assertIn('class="crumbs"', html)
        self.assertIn('<li><a href="/datasets/">Datasets</a></li>', html)

    def test_datasets_table_has_rows_column_and_filterable_rows(self):
        make_dataset(self.user, "A", "finance", is_processed=True)
        html = self.client.get("/datasets/").content.decode()
        self.assertIn('data-type="finance"', html)
        self.assertIn("data-search-item", html)
        self.assertIn(">Rows<", html)

    def test_decision_cards_hide_the_explanation_behind_a_why_toggle(self):
        from decisions.models import Decision
        dataset = make_dataset(self.user, "Q1", is_processed=True)
        Decision.objects.create(dataset=dataset, title="T", rule_name="R", domain="sales",
                                recommendation="r", explanation="Because of the data.", confidence=0.9)
        html = self.client.get(f"/datasets/{dataset.pk}/").content.decode()
        self.assertIn('<details class="why">', html)
        self.assertIn("<summary>Why?</summary>", html)
        self.assertIn("Because of the data.", html)  # readable without JavaScript

    def test_active_filters_are_removable_chips(self):
        html = self.client.get("/decisions/filtered/?domain=sales&confidence=high").content.decode()
        self.assertIn("Domain: Sales", html)
        self.assertIn('href="/decisions/filtered/?confidence=high"', html)
        self.assertIn('href="/decisions/filtered/?domain=sales"', html)


class DesignRuleGuards(SimpleTestCase):
    """The 'never use' list, as tests."""

    def read(self, path):
        return path.read_text(encoding="utf-8")

    def test_no_em_or_en_dashes_anywhere(self):
        for path in FILES_UNDER_RULES:
            with self.subTest(file=str(path.relative_to(ROOT))):
                text = self.read(path)
                self.assertNotIn("\u2014", text)
                self.assertNotIn("\u2013", text)
                self.assertNotIn("&mdash;", text)
                self.assertNotIn("&ndash;", text)

    def test_forbidden_css_and_js_features(self):
        css = re.sub(r"/\*.*?\*/", "", self.read(STYLE), flags=re.S)
        js = re.sub(r"/\*.*?\*/", "", self.read(SCRIPT), flags=re.S)
        for token in ("linear-gradient", "radial-gradient", "conic-gradient", "999px", "@keyframes",
                      "scroll-behavior", "backdrop-filter", "box-shadow", "text-shadow"):
            with self.subTest(token=token):
                self.assertNotIn(token, css)
        for token in ("IntersectionObserver", "scroll-behavior", "scrollIntoView", "mousemove", "requestAnimationFrame"):
            with self.subTest(token=token):
                self.assertNotIn(token, js)

    def test_only_allowed_cursors(self):
        css = self.read(STYLE)
        found = set(re.findall(r"cursor:\s*([\w-]+)", css))
        self.assertLessEqual(found, {"pointer", "default", "not-allowed"})

    def test_nothing_is_rounder_than_10px(self):
        css = self.read(STYLE)
        radii = [int(n) for n in re.findall(r"--r-[\w]+:\s*(\d+)px", css)]
        radii += [int(n) for n in re.findall(r"border-radius:\s*(\d+)px", css)]
        self.assertTrue(radii)
        self.assertLessEqual(max(radii), 10)
        self.assertNotRegex(css, r"border-radius:\s*\d+%")

    def test_palette_variables_are_exactly_the_specified_values(self):
        css = self.read(STYLE)
        expected = {
            "bg": "#F3EEE6", "oatmeal": "#E9E2D7", "surface": "#FBF8F3", "sand": "#DCC8B5",
            "ink": "#4D362B", "muted": "#6B5546", "coffee": "#8C6F5D", "primary": "#611E2F",
            "primary-hover": "#4A1623", "sage": "#A7B19A", "success-text": "#4A5D3F",
            "warning-text": "#8A5A12", "danger-text": "#A12B2B",
        }
        for name, value in expected.items():
            with self.subTest(var=name):
                self.assertRegex(css, rf"--{name}:\s*{value};")

    def test_no_hex_colour_outside_the_palette_in_css_rules(self):
        css = self.read(STYLE)
        root_end = css.index("}", css.index(":root"))
        rules = css[root_end:]
        self.assertEqual(re.findall(r"#[0-9A-Fa-f]{3,8}\b", rules), [])

    def test_no_external_urls_inline_styles_or_inline_scripts(self):
        for path in TEMPLATES:
            html = self.read(path)
            with self.subTest(template=path.name):
                self.assertNotRegex(html, r"(?:src|href|action)\s*=\s*\"(?:https?:)?//")
                self.assertNotRegex(html, r"\sstyle\s*=")
                self.assertNotRegex(html, r"<style\b")
                self.assertNotRegex(html, r"<script(?![^>]*\bsrc=)[^>]*>")
        for path in (STYLE, SCRIPT):
            self.assertNotRegex(self.read(path), r"https?://")

    def test_no_emoji_or_fake_social_proof_in_templates(self):
        emoji = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B50]")
        banned = ("testimonial", "trusted by", "built with", "made with", "customers love", "\u2605", "5 stars")
        for path in TEMPLATES:
            text = self.read(path)
            with self.subTest(template=path.name):
                self.assertIsNone(emoji.search(text))
                for phrase in banned:
                    self.assertNotIn(phrase, text.lower())

    def test_no_launch_wording(self):
        for path in TEMPLATES:
            text = self.read(path).lower()
            with self.subTest(template=path.name):
                self.assertNotRegex(text, r"\b(launched|now live|we are live|goes live)\b")

    def test_no_photographs_only_svg_and_css(self):
        for folder in ("static", "templates"):
            for path in (ROOT / folder).rglob("*"):
                self.assertNotIn(path.suffix.lower(), {".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif"}, str(path))
        for path in TEMPLATES:
            self.assertNotIn("<img", self.read(path), path.name)

    def test_at_most_one_stylesheet_and_one_script(self):
        self.assertEqual([p.name for p in (ROOT / "static").rglob("*.css")], ["app.css"])
        self.assertEqual([p.name for p in (ROOT / "static").rglob("*.js")], ["app.js"])
