"""Milestone 3 tests: every screen renders, uses only self-hosted assets, keeps its rules."""
import re
from pathlib import Path

from django.conf import settings
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase
from django.views.defaults import permission_denied, server_error

from bizmind.testing import (
    TempMediaMixin,
    csv_upload,
    make_dataset,
    make_user,
)
from datasets.models import Dataset
from datasets.validators import validate_csv_upload
from decisions.models import Decision

EXTERNAL = re.compile(r'\b(?:src|href|action)\s*=\s*"(?:https?:)?//', re.I)
INLINE_SCRIPT = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>", re.I)
INLINE_STYLE = re.compile(r"<style\b|\sstyle\s*=", re.I)


def add_decision(dataset, title, confidence, domain="sales"):
    return Decision.objects.create(
        dataset=dataset, title=title, rule_name=title.upper().replace(" ", "_"), domain=domain,
        recommendation="Do the thing.", explanation="Because of the data.", confidence=confidence,
        impact="Revenue could improve.",
    )


class EveryScreenIsCspSafeTests(TestCase):
    """Rendered pages: no inline code and nothing loaded from another host."""

    def setUp(self):
        self.user = make_user("analyst@example.com", "ANALYST")
        self.dataset = make_dataset(self.user, name="Q1 Sales", is_processed=True)
        add_decision(self.dataset, "Top product", 0.91)
        add_decision(self.dataset, "Revenue risk", 0.45, "finance")

    def assert_clean(self, html, label):
        self.assertIsNone(EXTERNAL.search(html), f"{label}: loads from another host")
        self.assertIsNone(INLINE_SCRIPT.search(html), f"{label}: inline <script>")
        self.assertIsNone(INLINE_STYLE.search(html), f"{label}: inline style")
        self.assertIn('lang="en"', html)
        self.assertEqual(html.count("<h1"), 1, f"{label}: needs exactly one h1")
        self.assertIn("<title>", html)

    def test_public_pages(self):
        for url in ("/", "/accounts/login/", "/accounts/signup/", "/nope/"):
            with self.subTest(url=url):
                self.assert_clean(self.client.get(url).content.decode(), url)

    def test_logged_in_pages(self):
        self.client.force_login(self.user)
        urls = [
            "/", "/dashboard/", "/datasets/", f"/datasets/{self.dataset.pk}/", "/datasets/upload/",
            "/decisions/filtered/", "/decisions/filtered/?domain=sales&confidence=high",
            f"/decisions/{self.dataset.pk}/", "/nope/",
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assert_clean(self.client.get(url).content.decode(), url)

    def test_error_pages_403_and_500(self):
        request = RequestFactory().get("/")
        request.user = self.user
        self.assert_clean(permission_denied(request, Exception()).content.decode(), "403")
        self.assert_clean(server_error(request).content.decode(), "500")

    def test_500_page_needs_no_context_or_static_lookup(self):
        html = render_to_string("500.html")  # rendered with no context at all
        self.assertIn("Something went wrong", html)
        self.assertIn('href=""', html)  # "Try again" link
        self.assertNotIn("{%", html)

    def test_swagger_docs_are_self_hosted(self):
        html = self.client.get("/api/docs/").content.decode()
        self.assertIsNone(EXTERNAL.search(html))
        self.assertNotIn("jsdelivr", html)
        self.assertIsNone(INLINE_SCRIPT.search(html))


class NavigationTests(TestCase):
    def nav(self, user=None):
        if user:
            self.client.force_login(user)
        html = self.client.get("/").content.decode()
        return re.search(r'<nav.*?</nav>', html, re.S).group(0)

    def test_visitor_nav(self):
        nav = self.nav()
        for text in ("Home", "Log in", "Sign up"):
            self.assertIn(text, nav)
        self.assertNotIn("Logout", nav)
        self.assertNotIn("Contact", nav)

    def test_analyst_nav_has_upload_and_a_post_logout_form(self):
        nav = self.nav(make_user("a@example.com", "ANALYST"))
        for text in ("Dashboard", "Datasets", "Decisions", "Upload", "Logout"):
            self.assertIn(text, nav)
        self.assertRegex(nav, r'<form method="post" action="/accounts/logout/"')
        self.assertIn("csrfmiddlewaretoken", nav)

    def test_viewer_nav_has_no_upload_link(self):
        nav = self.nav(make_user("v@example.com", "VIEWER"))
        self.assertNotIn("Upload", nav)
        self.assertIn("Logout", nav)

    def test_current_page_is_marked(self):
        self.client.force_login(make_user())
        html = self.client.get("/datasets/").content.decode()
        self.assertRegex(html, r'href="/datasets/" aria-current="page"')

    def test_footer_links_to_the_api_docs(self):
        self.assertIn('<a href="/api/docs/">API docs</a>', self.client.get("/").content.decode())


class HomeTests(TestCase):
    def test_about_text_is_merged_into_home(self):
        html = self.client.get("/").content.decode()
        self.assertIn("How it works", html)
        self.assertIn("About BizMind", html)

    def test_visitor_sees_signup_and_login_buttons(self):
        html = self.client.get("/").content.decode()
        self.assertIn('href="/accounts/signup/"', html)
        self.assertIn('href="/accounts/login/"', html)

    def test_logged_in_user_sees_a_dashboard_button_instead(self):
        self.client.force_login(make_user())
        html = self.client.get("/").content.decode()
        self.assertIn("Go to dashboard", html)


class AuthScreensTests(TestCase):
    def test_login_error_is_shown_and_form_has_a_loading_state(self):
        make_user("a@example.com")
        response = self.client.post("/accounts/login/", {"email": "a@example.com", "password": "bad"})
        self.assertContains(response, "Invalid email or password.")
        self.assertContains(response, 'data-loading-text="Signing in..."')

    def test_signup_field_errors_appear_under_the_field(self):
        response = self.client.post("/accounts/signup/", {"email": "bad", "password": "x"})
        self.assertContains(response, 'class="field-error"')
        self.assertContains(response, "has-error")
        self.assertContains(response, 'data-loading-text="Creating..."')


class DashboardScreenTests(TestCase):
    def test_first_use_strip_shows_sample_links_for_a_new_user(self):
        self.client.force_login(make_user())
        html = self.client.get("/dashboard/").content.decode()
        self.assertIn("Get started in three steps", html)
        for name in ("sales", "marketing", "finance"):
            self.assertIn(f"samples/{name}_sample.csv", html)
        self.assertNotIn("<progress", html)  # no charts until there is data

    def test_charts_are_plain_css_bars_not_a_chart_library(self):
        user = make_user()
        dataset = make_dataset(user, is_processed=True)
        add_decision(dataset, "A", 0.9)
        add_decision(dataset, "B", 0.5, "finance")
        add_decision(dataset, "C", 0.1, "finance")
        self.client.force_login(user)
        html = self.client.get("/dashboard/").content.decode()
        self.assertEqual(html.count("<progress"), 5)  # 3 confidence rows + 2 domains
        self.assertIn('value="1" max="3"', html)
        self.assertNotIn("<canvas", html)
        self.assertIn("/decisions/filtered/?confidence=high", html)
        self.assertIn("/decisions/filtered/?domain=finance", html)
        self.assertIn("High Confidence 0.90", html)  # word AND number, not colour alone

    def test_recent_decisions_table_and_empty_state(self):
        user = make_user()
        self.client.force_login(user)
        make_dataset(user, is_processed=True)
        self.assertIn("No decisions yet. Your data is within the expected ranges.",
                      self.client.get("/dashboard/").content.decode())


class DatasetScreensTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)

    def test_list_shows_status_words_and_decision_counts(self):
        done = make_dataset(self.user, "Done", is_processed=True)
        make_dataset(self.user, "Waiting", "finance")
        add_decision(done, "X", 0.8)
        html = self.client.get("/datasets/").content.decode()
        self.assertIn("Processed", html)
        self.assertIn("Pending", html)
        self.assertRegex(html, r'<td class="num">1</td>')

    def test_empty_list_offers_upload_and_samples(self):
        html = self.client.get("/datasets/").content.decode()
        self.assertIn("No datasets yet.", html)
        self.assertIn("samples/sales_sample.csv", html)

    def test_viewer_sees_no_upload_button_on_the_list(self):
        self.client.force_login(make_user("viewer@example.com", "VIEWER"))
        self.assertNotIn("Upload dataset", self.client.get("/datasets/").content.decode())

    def test_detail_shows_every_decision_field(self):
        dataset = make_dataset(self.user, "Q1", is_processed=True)
        add_decision(dataset, "Top product", 0.91)
        html = self.client.get(f"/datasets/{dataset.pk}/").content.decode()
        for text in ("Top product", "High Confidence 0.91", "Insight", "Recommendation",
                     "Explanation", "Action", "Impact", "Derived from deviation"):
            self.assertIn(text, html)

    def test_upload_page_lists_required_columns_per_type_and_has_a_loading_state(self):
        html = self.client.get("/datasets/upload/").content.decode()
        self.assertContains(self.client.get("/datasets/upload/"), 'data-loading-text="Processing..."')
        for column in ("units_sold", "impressions", "department"):
            self.assertIn(column, html)
        self.assertEqual(html.count("data-schema="), 3)
        self.assertIn("10 MB", html)

    def test_upload_errors_show_next_to_the_field(self):
        response = self.client.post(
            "/datasets/upload/",
            {"name": "X", "type": "sales", "file": csv_upload("date,product\n1,2\n")},
        )
        self.assertContains(response, "Missing required columns")
        self.assertContains(response, "has-error")


class DecisionsScreenTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)
        self.dataset = make_dataset(self.user, "Q1", is_processed=True)
        add_decision(self.dataset, "Sales one", 0.9)
        add_decision(self.dataset, "Finance one", 0.2, "finance")

    def test_filter_form_keeps_the_selected_values(self):
        html = self.client.get("/decisions/filtered/?domain=finance&confidence=low").content.decode()
        self.assertIn('<option value="finance" selected>', html)
        self.assertIn('<option value="low" selected>', html)
        self.assertIn("Finance one", html)
        self.assertNotIn("Sales one", html)

    def test_no_match_and_no_data_have_different_empty_messages(self):
        html = self.client.get("/decisions/filtered/?domain=marketing").content.decode()
        self.assertIn("No decisions match these filters.", html)
        Decision.objects.all().delete()
        html = self.client.get("/decisions/filtered/").content.decode()
        self.assertIn("No decisions yet.", html)

    def test_each_decision_links_to_its_dataset(self):
        html = self.client.get("/decisions/filtered/").content.decode()
        self.assertIn(f'href="/datasets/{self.dataset.pk}/"', html)


class SampleCsvTests(TempMediaMixin, TestCase):
    """The sample files promised on the dashboard and upload page really work."""

    def test_each_sample_passes_the_validator_and_produces_decisions(self):
        self.client.force_login(make_user())
        for kind in ("sales", "marketing", "finance"):
            data = Path(settings.BASE_DIR, f"static/samples/{kind}_sample.csv").read_bytes()
            with self.subTest(kind=kind):
                validate_csv_upload(csv_upload(data.decode()), kind)
                with self.captureOnCommitCallbacks(execute=True):
                    response = self.client.post(
                        "/datasets/upload/", {"name": kind, "type": kind, "file": csv_upload(data.decode())}
                    )
                self.assertEqual(response.status_code, 302)
                dataset = Dataset.objects.get(name=kind)
                self.assertTrue(dataset.is_processed)
                self.assertGreaterEqual(dataset.decisions.count(), 1)


class ErrorPageTests(TestCase):
    def test_404_page_for_visitors_and_for_someone_elses_dataset(self):
        owner = make_user("o@example.com")
        dataset = make_dataset(owner)
        self.assertContains(self.client.get("/nope/"), "Page not found", status_code=404)
        self.client.force_login(make_user("x@example.com"))
        response = self.client.get(f"/datasets/{dataset.pk}/")
        self.assertContains(response, "Page not found", status_code=404)
        self.assertContains(response, "Back to dashboard", status_code=404)

    def test_403_page_text(self):
        request = RequestFactory().get("/")
        request.user = make_user()
        self.assertIn("You are not allowed to do that", permission_denied(request, Exception()).content.decode())
