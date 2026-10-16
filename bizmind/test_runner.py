"""Test runner that keeps the test suite isolated from the real environment.

Used only by ``python manage.py test`` (see TEST_RUNNER in settings.py).
It never runs in production, so it cannot change how the app behaves.

While tests run it:
1. points MEDIA_ROOT at a temporary folder, so uploads never land in the
   real ``media/`` folder, and deletes that folder when the run finishes (S9);
2. uses Django's plain static-files storage, because the production
   WhiteNoise "manifest" storage crashes on ``{% static %}`` unless
   ``collectstatic`` has been run first;
3. turns off the HTTPS redirect, because with DEBUG=False every test
   request would otherwise be answered with a 301 redirect to https;
4. uses a fast (insecure) password hasher so tests that create users run
   in milliseconds instead of seconds;
5. replaces the cache with a dummy one, so rate-limit counters from one
   test can never block another (throttle tests opt back in);
6. hides WhiteNoise's "No directory at: .../staticfiles/" warning, which
   only means collectstatic has not been run (not needed for tests).
"""
import shutil
import tempfile
import warnings

from django.conf import settings
from django.test import override_settings
from django.test.runner import DiscoverRunner


class BizMindTestRunner(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)

        warnings.filterwarnings("ignore", message="No directory at", category=UserWarning)

        self._temp_media_root = tempfile.mkdtemp(prefix="bizmind-test-media-")

        storages = dict(settings.STORAGES)
        storages["staticfiles"] = {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        }

        self._settings_override = override_settings(
            MEDIA_ROOT=self._temp_media_root,
            STORAGES=storages,
            SECURE_SSL_REDIRECT=False,
            PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
            CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}},
        )
        self._settings_override.enable()

    def teardown_test_environment(self, **kwargs):
        self._settings_override.disable()
        shutil.rmtree(self._temp_media_root, ignore_errors=True)
        super().teardown_test_environment(**kwargs)
