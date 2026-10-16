import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import unquote, urlparse

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required.")

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
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "bizmind.urls"

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

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///db.sqlite3")


def database_config(url):
    parsed = urlparse(url)

    if parsed.scheme == "sqlite":
        database_name = parsed.path.lstrip("/") or "db.sqlite3"
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / database_name,
        }

    if parsed.scheme in {"postgres", "postgresql"}:
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": parsed.path.lstrip("/"),
            "USER": unquote(parsed.username or ""),
            "PASSWORD": unquote(parsed.password or ""),
            "HOST": parsed.hostname or "",
            "PORT": str(parsed.port or ""),
            "CONN_MAX_AGE": 600,
            "CONN_HEALTH_CHECKS": True,
        }

    raise ValueError("DATABASE_URL must use sqlite:// or postgresql://")


DATABASES = {"default": database_config(DATABASE_URL)}

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

# Rate-limit counters (login, signup, token endpoints) live here. LocMemCache is
# per process: fine for the single gunicorn worker used today; with several
# workers each would count separately, so move to a shared cache then.
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

# Sent with every response: another site only learns that the request came from
# BizMind itself, never the full URL (which can contain dataset ids).
SECURE_REFERRER_POLICY = "same-origin"

# Content-Security-Policy: tells the browser which sources may load scripts,
# styles, fonts and images, and what the page may submit forms to or be framed by.
# The pages TODAY still load AOS (unpkg), Font Awesome (cdnjs) and Chart.js
# (jsDelivr), and use inline <script> blocks, so those are allowed for now.
# TODO Milestone 3: self-host everything, then remove every https:// source and
# "'unsafe-inline'" below (docs/02_TRD.md: "allows only self-hosted assets").
# bizmind/test_security_headers.py fails if a template uses a host not listed here.
CONTENT_SECURITY_POLICY = {
    "default-src": ["'self'"],
    "script-src": ["'self'", "'unsafe-inline'", "https://unpkg.com", "https://cdn.jsdelivr.net"],
    "style-src": [
        "'self'", "'unsafe-inline'",
        "https://unpkg.com", "https://cdnjs.cloudflare.com", "https://cdn.jsdelivr.net",
    ],
    "font-src": ["'self'", "https://cdnjs.cloudflare.com"],
    "img-src": ["'self'", "data:", "https://cdn.jsdelivr.net"],  # jsDelivr: Swagger favicon
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
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

REST_FRAMEWORK = {
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
}

SPECTACULAR_SETTINGS = {
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
