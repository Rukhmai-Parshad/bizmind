import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import unquote, urlparse

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Security audit SEC-1. Environment variables read by this file (see .env.example):
#   required in production: SECRET_KEY, DATABASE_URL
#   optional: DEBUG, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, RENDER_EXTERNAL_HOSTNAME,
#             NUM_PROXIES, ADMIN_URL, DATABASE_SSL_REQUIRE, HSTS_SECONDS


def env_flag(name):
    """True only when the variable is exactly "true" (any letter case)."""
    return os.getenv(name, "").strip().lower() == "true"


SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY environment variable is required. Set it in .env (local) "
        "or in the Render dashboard (production)."
    )

DEBUG = os.getenv("DEBUG", "False").lower() == "true"

configured_hosts = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "").split(",")
    if host.strip()
]
render_hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME")

ALLOWED_HOSTS = configured_hosts or (
    [render_hostname] if render_hostname else []
)

configured_origins = [
    origin.strip()
    for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

CSRF_TRUSTED_ORIGINS = configured_origins or (
    [f"https://{render_hostname}"] if render_hostname else []
)

INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',  # remembers used/revoked refresh tokens
    'drf_spectacular',
    'drf_spectacular_sidecar',  # self-hosted Swagger UI files (no CDN)

    # Local apps
    'accounts',
    'datasets',
    'sales',
    'marketing',
    'finance',
    'decisions',
    'dashboard',
    'core',
    'api',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "bizmind.middleware.ContentSecurityPolicyMiddleware",
    "bizmind.middleware.PermissionsPolicyMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "bizmind.urls"

# Where the Django admin lives. Not /admin/, which every scanner tries first.
# This only hides the page; the real protection is that the admin accepts staff
# accounts only and that its login is rate limited (accounts/admin_security.py).
# Set ADMIN_URL in the environment to pick your own path.
ADMIN_URL = (os.getenv("ADMIN_URL") or "").strip().strip("/") or "site-admin"
ADMIN_URL += "/"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "bizmind.wsgi.application"

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    if not DEBUG:
        # Without this, production would silently fall back to a throw-away
        # SQLite file and lose data on the next deploy.
        raise RuntimeError(
            "DATABASE_URL environment variable is required when DEBUG is not True. "
            "Set it in the Render dashboard (or to sqlite:///db.sqlite3 in .env)."
        )
    DATABASE_URL = "sqlite:///db.sqlite3"

# Off by default. Set DATABASE_SSL_REQUIRE=true to make PostgreSQL connections
# fail unless they are encrypted (sslmode=require). See docs/SECURITY_AUDIT.md
# for how to test this before turning it on.
DATABASE_SSL_REQUIRE = env_flag("DATABASE_SSL_REQUIRE")


def database_config(url, ssl_require=False):
    parsed = urlparse(url)

    if parsed.scheme == "sqlite":
        database_name = parsed.path.lstrip("/") or "db.sqlite3"
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / database_name,
        }

    if parsed.scheme in {"postgres", "postgresql"}:
        config = {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": parsed.path.lstrip("/"),
            "USER": unquote(parsed.username or ""),
            "PASSWORD": unquote(parsed.password or ""),
            "HOST": parsed.hostname or "",
            "PORT": str(parsed.port or ""),
            "CONN_MAX_AGE": 600,
            "CONN_HEALTH_CHECKS": True,
        }
        if ssl_require:
            config["OPTIONS"] = {"sslmode": "require"}
        return config

    raise ValueError("DATABASE_URL must use sqlite:// or postgresql://")


DATABASES = {"default": database_config(DATABASE_URL, DATABASE_SSL_REQUIRE)}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Rate-limit counters (login, signup, admin login, token endpoints) live here.
# LocMemCache is per process: fine for the single gunicorn worker used today.
# With N workers each worker counts separately, so the real limit becomes about
# N times higher (gunicorn also reads WEB_CONCURRENCY). Counters are also lost
# on every restart or deploy. Move to a shared cache (database or Redis) before
# adding workers.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
}

# How many trusted reverse proxies sit in front of the app (Render, nginx...).
# 0 = ignore X-Forwarded-For and use the connecting address. Set this correctly
# in production, otherwise IP-based limits see every user as the same address.
NUM_PROXIES = int(os.getenv("NUM_PROXIES", "0"))

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Cookies: HttpOnly (JavaScript cannot read them; app.js never reads cookies, forms
# carry the CSRF token in a hidden field) and SameSite=Lax (not sent on cross-site
# POSTs). The Secure flag is added below when DEBUG is off.
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"

# Sent with every response: another site only learns that the request came from
# BizMind itself, never the full URL (which can contain dataset ids).
SECURE_REFERRER_POLICY = "same-origin"

# Permissions-Policy: BizMind uses none of these browser features, so every page
# switches them off (also for anything embedded in the page). Sent by
# bizmind.middleware.PermissionsPolicyMiddleware. An empty list means "nobody".
PERMISSIONS_POLICY = {
    "accelerometer": [],
    "camera": [],
    "geolocation": [],
    "gyroscope": [],
    "magnetometer": [],
    "microphone": [],
    "payment": [],
    "usb": [],
}

# Content-Security-Policy: tells the browser which sources may load scripts,
# styles, fonts and images, and what the page may submit forms to or be framed by.
# Everything is self-hosted (static/css/app.css, static/js/app.js), so every
# source is 'self' only: no CDN hosts and no 'unsafe-inline'. That also means
# templates must not contain inline <script>, <style> or style="..." attributes.
# bizmind/test_security_headers.py fails if this policy or a template regresses.
CONTENT_SECURITY_POLICY = {
    "default-src": ["'self'"],
    "script-src": ["'self'"],
    "style-src": ["'self'"],
    "font-src": ["'self'"],
    "img-src": ["'self'", "data:"],  # data: is used for the inline SVG favicon
    "connect-src": ["'self'"],
    "object-src": ["'none'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'"],
    "frame-ancestors": ["'none'"],
}

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # One year by default. Set HSTS_SECONDS to a smaller number to shorten it.
    SECURE_HSTS_SECONDS = int(os.getenv("HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# JSON only in production: the browsable API is an HTML page that can show forms
# and would need extra CSRF care. It stays available when DEBUG is True.
API_RENDERER_CLASSES = ["rest_framework.renderers.JSONRenderer"]
if DEBUG:
    API_RENDERER_CLASSES.append("rest_framework.renderers.BrowsableAPIRenderer")

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": API_RENDERER_CLASSES,
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Limits for the token endpoints (api/throttles.py).
    "DEFAULT_THROTTLE_RATES": {
        "auth_ip": "30/min",      # per IP address
        "auth_account": "5/min",  # per account (email in the request body)
    },
    "NUM_PROXIES": NUM_PROXIES,
}

SIMPLE_JWT = {
    # Short-lived access token: if it leaks, it is useless after 15 minutes.
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    # Every refresh gives a NEW refresh token and the old one is blacklisted,
    # so a stolen refresh token stops working as soon as the real client refreshes.
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    # Pinned to the library defaults so a future upgrade cannot change them silently.
    # Tokens are signed with SECRET_KEY, so changing SECRET_KEY logs everyone out.
    # UPDATE_LAST_LOGIN must stay False: the User model has no last_login column.
    "ALGORITHM": "HS256",
    "UPDATE_LAST_LOGIN": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

SPECTACULAR_SETTINGS = {
    # Serve Swagger UI from our own static files instead of a CDN (CSP is 'self' only).
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "TITLE": "BizMind API",
    "DESCRIPTION": (
        "REST API for BizMind — a Unified Decision Intelligence Platform "
        "that transforms business data into actionable insights and decisions."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# Used only by "manage.py test": temporary MEDIA_ROOT and test-safe settings.
TEST_RUNNER = "bizmind.test_runner.BizMindTestRunner"
