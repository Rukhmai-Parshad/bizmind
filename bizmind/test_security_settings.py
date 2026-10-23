"""SEC-1 tests: environment variables, production settings and response headers.

The settings file is executed again here with a made-up environment (a copy
under another module name), so these tests prove what production WOULD load
whatever DEBUG your own .env has. They never touch the real settings or the
real environment, and the fake values below are not real secrets.
"""
import importlib.util
import os
from datetime import timedelta
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.test import SimpleTestCase, TestCase

from bizmind.middleware import build_permissions_policy_header
from bizmind.testing import make_user

SETTINGS_FILE = Path(settings.BASE_DIR) / "bizmind" / "settings.py"
FAKE_SECRET = "fake-secret-key-for-tests-only-0123456789abcdef"
FAKE_DB = "postgresql://dbuser:dbpass@db.example.internal:5432/bizmind"
PROD = {"SECRET_KEY": FAKE_SECRET, "DATABASE_URL": FAKE_DB, "RENDER_EXTERNAL_HOSTNAME": "bizmind.example.com"}


def load_settings(env):
    """Run settings.py with ONLY these environment variables and no .env file."""
    spec = importlib.util.spec_from_file_location("bizmind_settings_probe", SETTINGS_FILE)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(os.environ, env, clear=True), mock.patch("dotenv.load_dotenv"):
        spec.loader.exec_module(module)
    return module


class FailFastTests(SimpleTestCase):
    def test_missing_secret_key_stops_the_app_with_a_clear_message(self):
        with self.assertRaises(RuntimeError) as caught:
            load_settings({"DATABASE_URL": FAKE_DB})
        self.assertIn("SECRET_KEY", str(caught.exception))

    def test_empty_secret_key_counts_as_missing(self):
        with self.assertRaises(RuntimeError):
            load_settings({"SECRET_KEY": "", "DATABASE_URL": FAKE_DB})

    def test_missing_database_url_stops_production(self):
        with self.assertRaises(RuntimeError) as caught:
            load_settings({"SECRET_KEY": FAKE_SECRET})
        message = str(caught.exception)
        self.assertIn("DATABASE_URL", message)
        self.assertNotIn(FAKE_SECRET, message)  # an error must never print a secret

    def test_missing_database_url_is_fine_in_local_debug_mode(self):
        loaded = load_settings({"SECRET_KEY": FAKE_SECRET, "DEBUG": "True"})
        self.assertEqual(loaded.DATABASES["default"]["ENGINE"], "django.db.backends.sqlite3")

    def test_only_those_two_variables_are_required_in_production(self):
        loaded = load_settings({"SECRET_KEY": FAKE_SECRET, "DATABASE_URL": FAKE_DB})
        self.assertFalse(loaded.DEBUG)

    def test_unknown_database_scheme_is_still_refused(self):
        with self.assertRaises(ValueError):
            load_settings({"SECRET_KEY": FAKE_SECRET, "DATABASE_URL": "mysql://u:p@h/db"})


class ProductionSettingsTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.prod = load_settings(PROD)

    def test_debug_is_off_by_default(self):
        self.assertIs(self.prod.DEBUG, False)

    def test_debug_needs_the_exact_word_true(self):
        for value in ("1", "yes", "on", "false", ""):
            with self.subTest(value=value):
                self.assertIs(load_settings({**PROD, "DEBUG": value}).DEBUG, False)
        self.assertIs(load_settings({**PROD, "DEBUG": "True"}).DEBUG, True)

    def test_hosts_and_csrf_origins_come_from_the_environment(self):
        self.assertEqual(self.prod.ALLOWED_HOSTS, ["bizmind.example.com"])
        self.assertEqual(self.prod.CSRF_TRUSTED_ORIGINS, ["https://bizmind.example.com"])
        loaded = load_settings({**PROD, "ALLOWED_HOSTS": "a.example, b.example", "CSRF_TRUSTED_ORIGINS": "https://a.example"})
        self.assertEqual(loaded.ALLOWED_HOSTS, ["a.example", "b.example"])
        self.assertEqual(loaded.CSRF_TRUSTED_ORIGINS, ["https://a.example"])

    def test_no_wildcard_host_by_default(self):
        self.assertNotIn("*", load_settings({"SECRET_KEY": FAKE_SECRET, "DATABASE_URL": FAKE_DB}).ALLOWED_HOSTS)

    def test_https_settings_are_on(self):
        self.assertTrue(self.prod.SECURE_SSL_REDIRECT)
        self.assertGreaterEqual(self.prod.SECURE_HSTS_SECONDS, 31536000)
        self.assertTrue(self.prod.SECURE_HSTS_INCLUDE_SUBDOMAINS)
        self.assertEqual(self.prod.SECURE_PROXY_SSL_HEADER, ("HTTP_X_FORWARDED_PROTO", "https"))

    def test_hsts_length_can_be_lowered_from_the_environment(self):
        self.assertEqual(load_settings({**PROD, "HSTS_SECONDS": "300"}).SECURE_HSTS_SECONDS, 300)

    def test_cookies_are_secure_httponly_and_samesite(self):
        self.assertTrue(self.prod.SESSION_COOKIE_SECURE)
        self.assertTrue(self.prod.CSRF_COOKIE_SECURE)
        self.assertTrue(self.prod.SESSION_COOKIE_HTTPONLY)
        self.assertTrue(self.prod.CSRF_COOKIE_HTTPONLY)
        self.assertEqual(self.prod.SESSION_COOKIE_SAMESITE, "Lax")
        self.assertEqual(self.prod.CSRF_COOKIE_SAMESITE, "Lax")

    def test_framing_sniffing_and_referrer_settings(self):
        self.assertEqual(self.prod.X_FRAME_OPTIONS, "DENY")
        self.assertTrue(self.prod.SECURE_CONTENT_TYPE_NOSNIFF)
        self.assertEqual(self.prod.SECURE_REFERRER_POLICY, "same-origin")

    def test_the_content_security_policy_is_unchanged(self):
        self.assertEqual(self.prod.CONTENT_SECURITY_POLICY, settings.CONTENT_SECURITY_POLICY)

    def test_permissions_middleware_is_installed(self):
        self.assertIn("bizmind.middleware.PermissionsPolicyMiddleware", self.prod.MIDDLEWARE)

    def test_the_browsable_api_is_off_in_production_and_on_in_debug(self):
        browsable = "rest_framework.renderers.BrowsableAPIRenderer"
        self.assertEqual(
            self.prod.REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"],
            ["rest_framework.renderers.JSONRenderer"],
        )
        debug = load_settings({**PROD, "DEBUG": "True"})
        self.assertIn(browsable, debug.REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"])

    def test_the_admin_url_has_a_safe_default_and_can_be_changed(self):
        self.assertEqual(self.prod.ADMIN_URL, "site-admin/")
        for value, expected in (
            ("my-private-panel", "my-private-panel/"),
            ("/my-private-panel/ ", "my-private-panel/"),
            ("", "site-admin/"),
            ("/", "site-admin/"),
        ):
            with self.subTest(value=value):
                self.assertEqual(load_settings({**PROD, "ADMIN_URL": value}).ADMIN_URL, expected)

    def test_database_ssl_is_off_unless_the_switch_is_set(self):
        self.assertNotIn("OPTIONS", self.prod.DATABASES["default"])
        for value in ("false", "1", "yes", ""):
            with self.subTest(value=value):
                loaded = load_settings({**PROD, "DATABASE_SSL_REQUIRE": value})
                self.assertNotIn("OPTIONS", loaded.DATABASES["default"])

    def test_database_ssl_switch_requires_encrypted_connections(self):
        loaded = load_settings({**PROD, "DATABASE_SSL_REQUIRE": "true"})
        self.assertEqual(loaded.DATABASES["default"]["OPTIONS"], {"sslmode": "require"})

    def test_database_ssl_switch_does_not_touch_sqlite(self):
        loaded = load_settings({"SECRET_KEY": FAKE_SECRET, "DEBUG": "True", "DATABASE_SSL_REQUIRE": "true"})
        self.assertNotIn("OPTIONS", loaded.DATABASES["default"])

    def test_database_url_is_split_into_its_parts(self):
        config = self.prod.DATABASES["default"]
        self.assertEqual(config["NAME"], "bizmind")
        self.assertEqual(config["HOST"], "db.example.internal")


class JwtAndSessionSettingsTests(SimpleTestCase):
    def test_jwt_lifetimes_and_rotation(self):
        jwt = load_settings(PROD).SIMPLE_JWT
        self.assertLessEqual(jwt["ACCESS_TOKEN_LIFETIME"], timedelta(minutes=15))
        self.assertLessEqual(jwt["REFRESH_TOKEN_LIFETIME"], timedelta(days=7))
        self.assertTrue(jwt["ROTATE_REFRESH_TOKENS"])
        self.assertTrue(jwt["BLACKLIST_AFTER_ROTATION"])

    def test_jwt_pins(self):
        jwt = load_settings(PROD).SIMPLE_JWT
        self.assertEqual(jwt["ALGORITHM"], "HS256")
        self.assertIs(jwt["UPDATE_LAST_LOGIN"], False)  # the User model has no last_login
        self.assertEqual(jwt["AUTH_HEADER_TYPES"], ("Bearer",))

    def test_session_cookie_age_is_not_extended(self):
        loaded = load_settings(PROD)
        self.assertLessEqual(getattr(loaded, "SESSION_COOKIE_AGE", 1209600), 1209600)

    def test_throttle_rates_for_the_token_endpoints_are_set(self):
        rates = load_settings(PROD).REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
        self.assertEqual(set(rates), {"auth_ip", "auth_account"})


class PermissionsPolicyTests(TestCase):
    def test_header_text(self):
        self.assertEqual(
            build_permissions_policy_header({"camera": [], "fullscreen": ["self"]}),
            "camera=(), fullscreen=(self)",
        )

    def test_header_is_on_pages_api_errors_and_redirects(self):
        user = make_user()
        urls = ("/", "/accounts/login/", "/api/datasets/", "/dashboard/", "/no-such-page/", "/api/docs/")
        for url in urls:
            with self.subTest(url=url):
                header = self.client.get(url).headers["Permissions-Policy"]
                for feature in ("camera=()", "microphone=()", "geolocation=()", "payment=()"):
                    self.assertIn(feature, header)
        self.client.force_login(user)
        self.assertIn("Permissions-Policy", self.client.get("/dashboard/").headers)

    def test_all_security_headers_are_present_together(self):
        headers = self.client.get("/accounts/login/").headers
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(headers["X-Frame-Options"], "DENY")
        self.assertEqual(headers["Referrer-Policy"], "same-origin")
        self.assertIn("Content-Security-Policy", headers)
        self.assertIn("Permissions-Policy", headers)


class ExposedFilesTests(TestCase):
    def test_uploaded_files_are_not_served_from_media(self):
        self.assertEqual(self.client.get("/media/datasets/anything.csv").status_code, 404)
