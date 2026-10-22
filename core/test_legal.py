"""The legal pages must stay true to the code: numbers come from settings, cookies from real responses."""
import re
from pathlib import Path

from django.conf import settings
from django.test import Client, SimpleTestCase, TestCase

from accounts import ratelimit
from bizmind.testing import PASSWORD, make_dataset, make_user

ROOT = Path(settings.BASE_DIR)
EMAIL = "rukhmaiparshad@gmail.com"
DATE = "Last updated: 20 October 2026"
LEGAL = ("/privacy/", "/terms/", "/cookies/")


def text(client, url):
    return client.get(url).content.decode()


class LegalPagesBasicsTests(TestCase):
    def test_all_three_pages_load_for_visitors_and_users(self):
        for who in ("visitor", "user"):
            client = Client()
            if who == "user":
                client.force_login(make_user())
            for url in LEGAL:
                with self.subTest(url=url, who=who):
                    self.assertEqual(client.get(url).status_code, 200)

    def test_every_page_has_the_contact_details_and_a_fresh_date_and_no_placeholders(self):
        for url in LEGAL:
            html = text(self.client, url)
            with self.subTest(url=url):
                self.assertIn("Rukhmai Parshad", html)
                self.assertIn(EMAIL, html)
                self.assertIn(DATE, html)
                self.assertNotRegex(html, r"\[[A-Z ]{4,}\]")

    def test_privacy_terms_and_cookies_are_linked_from_every_footer(self):
        pages = {
            "landing footer": text(self.client, "/"),
            "privacy page footer": text(self.client, "/privacy/"),
            "cookies page footer": text(self.client, "/cookies/"),
            "login page": text(self.client, "/accounts/login/"),
            "signup page": text(self.client, "/accounts/signup/"),
            "404 page footer": text(self.client, "/nope/"),
        }
        self.client.force_login(make_user())
        for url in ("/dashboard/", "/datasets/", "/decisions/filtered/", "/accounts/settings/"):
            pages[f"app footer {url}"] = text(self.client, url)
        for label, html in pages.items():
            for href in ('href="/privacy/"', 'href="/terms/"', 'href="/cookies/"'):
                with self.subTest(page=label, link=href):
                    self.assertIn(href, html)

    def test_the_api_docs_link_is_still_in_the_footer(self):
        self.assertIn('<a href="/api/docs/">API docs</a>', text(self.client, "/"))


class PrivacyPolicyTests(TestCase):
    def setUp(self):
        self.html = text(self.client, "/privacy/")
        self.low = self.html.lower()

    def test_covers_what_the_dpdp_act_asks_a_notice_to_cover(self):
        for needed in (
            "digital personal data protection act, 2023", "data fiduciary", "data principal",
            "why we process your data", "what we collect, and why", "retention and deletion",
            "your rights", "access:", "correction:", "erasure:", "grievance:",
            "withdraw it at any time", "if there is a data breach", "data protection board of india",
            "aged 18 or over", "your consent",
        ):
            with self.subTest(topic=needed):
                self.assertIn(needed, self.low)

    def test_grievance_contact_is_a_working_mailto_link(self):
        self.assertIn(f'href="mailto:{EMAIL}"', self.html)

    def test_every_personal_data_item_in_the_code_is_listed(self):
        for item in ("email address", "password", "role", "consent record", "account creation date",
                     "dataset name", "rows parsed", "decisions generated", "login session record",
                     "refresh token records", "login and sign up counters", "application error logs"):
            with self.subTest(item=item):
                self.assertIn(item, self.low)

    def test_retention_numbers_match_the_settings(self):
        days = settings.SESSION_COOKIE_AGE // 86400
        self.assertIn(f"up to {days} days from login", self.low)
        refresh = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].days
        self.assertIn(f"<td>{refresh} days. expired records", self.low)
        self.assertIn(f"{ratelimit.LOGIN_WINDOW_SECONDS // 60} minutes for logins", self.low)
        self.assertEqual(ratelimit.SIGNUP_WINDOW_SECONDS, 3600)
        self.assertIn("one hour for sign ups", self.low)

    def test_hosting_region_matches_render_yaml(self):
        yaml = (ROOT / "render.yaml").read_text()
        self.assertEqual(len(re.findall(r"region:\s*singapore", yaml)), 2)  # web service and database
        self.assertIn("singapore region", self.low)
        self.assertIn("outside india", self.low)

    def test_expired_sessions_and_tokens_really_are_cleared_on_deploy(self):
        build = (ROOT / "build.sh").read_text()
        self.assertIn("manage.py clearsessions", build)
        self.assertIn("manage.py flushexpiredtokens", build)

    def test_the_app_really_sends_no_email(self):
        offenders = []
        for path in ROOT.rglob("*.py"):
            parts = set(path.parts)
            if {"venv", "migrations", "node_modules"} & parts or path.name.startswith("test"):
                continue
            if re.search(r"send_mail|send_mass_mail|EmailMessage|EMAIL_HOST", path.read_text(encoding="utf-8", errors="ignore")):
                offenders.append(str(path))
        self.assertEqual(offenders, [])
        self.assertIn("sends no emails by itself", self.low)

    def test_it_says_what_is_not_collected_and_that_third_parties_are_not_used(self):
        for claim in ("does not ask for your name", "does not record when you last logged in",
                      "no analytics, advertising or tracking", "loads no third party scripts"):
            self.assertIn(claim, self.low)

    def test_it_explains_deletion_and_points_to_settings(self):
        self.assertIn("open settings and choose delete my account", self.low)
        self.assertIn("deletes your account, datasets, rows and decisions at once", self.low)

    def test_it_says_the_cookie_details_live_on_the_cookie_page(self):
        self.assertIn('href="/cookies/"', self.html)

    def test_it_does_not_overclaim(self):
        for banned in ("fully compliant", "100% secure", "guarantee", "military grade", "bank grade"):
            self.assertNotIn(banned, self.low)


class CookiePolicyTests(TestCase):
    def test_lists_exactly_the_three_real_cookies_with_purpose_and_duration(self):
        html = text(self.client, "/cookies/")
        for name in ("sessionid", "csrftoken", "messages"):
            self.assertIn(f"<code>{name}</code>", html)
        self.assertEqual(len(re.findall(r"<tr><td><code>", html)), 3)

    def test_durations_match_the_settings(self):
        html = text(self.client, "/cookies/")
        self.assertIn(f"{settings.SESSION_COOKIE_AGE // 86400} days from login", html)
        self.assertIn(f"{settings.CSRF_COOKIE_AGE // 86400} days.", html)

    def test_states_there_are_no_analytics_or_advertising_cookies_and_no_banner(self):
        low = text(self.client, "/cookies/").lower()
        self.assertIn("no analytics cookies and no advertising cookies", low)
        self.assertIn("does not show a cookie banner", low)
        self.assertIn("no browser storage such as local storage", low)

    def test_no_page_shows_a_consent_banner(self):
        self.client.force_login(make_user())
        for url in ("/", "/accounts/login/", "/dashboard/", "/privacy/", "/cookies/"):
            low = text(self.client, url).lower()
            with self.subTest(url=url):
                for marker in ("cookie-banner", "accept all", "accept cookies", "cookie consent", "we use cookies"):
                    self.assertNotIn(marker, low)

    def test_the_app_sets_no_cookies_other_than_the_three_listed(self):
        """A new cookie anywhere in the app makes this fail, so the policy has to be updated first."""
        make_user("tour@example.com", "ANALYST")
        client = Client()
        seen = set()

        def visit(method, url, data=None):
            response = getattr(client, method)(url, data or {})
            seen.update(response.cookies.keys())
            seen.update(client.cookies.keys())

        for url in ("/", "/accounts/login/", "/accounts/signup/", "/privacy/", "/terms/", "/cookies/", "/nope/", "/favicon.ico", "/api/docs/"):
            visit("get", url)
        visit("post", "/accounts/login/", {"email": "tour@example.com", "password": PASSWORD})
        for url in ("/dashboard/", "/datasets/", "/datasets/upload/", "/decisions/filtered/", "/accounts/settings/", "/accounts/settings/delete/"):
            visit("get", url)
        visit("post", "/accounts/logout/")
        self.assertLessEqual(seen, {"sessionid", "csrftoken", "messages"})
        self.assertEqual(seen, {"sessionid", "csrftoken", "messages"})

    def test_measured_cookie_lifetimes_and_flags_match_the_policy(self):
        make_user("tour@example.com")
        login = self.client.post("/accounts/login/", {"email": "tour@example.com", "password": PASSWORD})
        self.assertEqual(int(login.cookies["sessionid"]["max-age"]), settings.SESSION_COOKIE_AGE)
        self.assertTrue(login.cookies["sessionid"]["httponly"])
        self.assertEqual(login.cookies["sessionid"]["samesite"], "Lax")
        self.assertEqual(int(login.cookies["csrftoken"]["max-age"]), settings.CSRF_COOKIE_AGE)
        self.assertEqual(login.cookies["csrftoken"]["samesite"], "Lax")
        logout = self.client.post("/accounts/logout/")
        self.assertEqual(logout.cookies["messages"]["max-age"], "")  # session cookie: gone when the browser closes
        self.assertTrue(logout.cookies["messages"]["httponly"])

    def test_cookies_are_secure_in_production_settings(self):
        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)
        # SECURE flags are tied to DEBUG=False in settings.py (see the cookie policy wording).
        source = (ROOT / "bizmind/settings.py").read_text()
        self.assertRegex(source, r"SESSION_COOKIE_SECURE\s*=\s*True")
        self.assertRegex(source, r"CSRF_COOKIE_SECURE\s*=\s*True")


class TermsTests(TestCase):
    def test_terms_match_the_new_behaviour(self):
        low = text(self.client, "/terms/").lower()
        for claim in ("aged 18 or over", "delete your account yourself at any time in settings",
                      "laws of india", "not financial, legal, tax or investment advice",
                      "leave out personal data about other people", 'href="/cookies/"', 'href="/privacy/"'):
            with self.subTest(claim=claim):
                self.assertIn(claim, low)

    def test_there_is_no_refund_or_payment_wording_because_there_is_no_payment_code(self):
        for path in ROOT.rglob("*.py"):
            if {"venv", "migrations"} & set(path.parts) or path.name.startswith("test"):
                continue
            self.assertNotRegex(path.read_text(encoding="utf-8", errors="ignore").lower(), r"stripe|razorpay|paypal|paytm|invoice|checkout")
        self.assertNotIn("refund", text(self.client, "/terms/").lower())


class NoThirdPartyTests(SimpleTestCase):
    def test_no_embeds_prefetch_hints_or_third_party_hosts_in_templates_or_static(self):
        patterns = {
            "iframe/embed/object": re.compile(r"<(iframe|embed|object)\b", re.I),
            "preconnect/dns-prefetch": re.compile(r'rel="(preconnect|dns-prefetch|preload)"', re.I),
            "external host": re.compile(r'(?:src|href|action)\s*=\s*"(?:https?:)?//', re.I),
            "known tracker": re.compile(r"google-analytics|googletagmanager|gtag\(|fbq\(|hotjar|mixpanel|segment\.com|sentry|doubleclick|adsbygoogle", re.I),
            "font host": re.compile(r"fonts\.googleapis|fonts\.gstatic|use\.typekit|fontawesome", re.I),
        }
        files = list((ROOT / "templates").rglob("*.html")) + [ROOT / "static/css/app.css", ROOT / "static/js/app.js"]
        for path in files:
            body = path.read_text(encoding="utf-8")
            for label, pattern in patterns.items():
                with self.subTest(file=path.name, rule=label):
                    self.assertIsNone(pattern.search(body))

    def test_the_csp_still_allows_only_self(self):
        for directive, sources in settings.CONTENT_SECURITY_POLICY.items():
            with self.subTest(directive=directive):
                self.assertLessEqual(set(sources), {"'self'", "'none'", "data:"})
