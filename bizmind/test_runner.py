"""Django test runner that keeps uploads out of the project media/ folder."""

from __future__ import annotations

import shutil
import tempfile

from django.test.runner import DiscoverRunner
from django.test.utils import override_settings


class IsolatedMediaTestRunner(DiscoverRunner):
    """Point MEDIA_ROOT at a temp directory for the whole test run, then delete it."""

    def setup_test_environment(self, **kwargs):
        self._media_root = tempfile.mkdtemp(prefix="bizmind-test-media-")
        self._settings_override = override_settings(
            MEDIA_ROOT=self._media_root,
            SECURE_SSL_REDIRECT=False,
            STORAGES={
                "default": {
                    "BACKEND": "django.core.files.storage.FileSystemStorage",
                },
                "staticfiles": {
                    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
                },
            },
        )
        self._settings_override.enable()
        super().setup_test_environment(**kwargs)

    def teardown_test_environment(self, **kwargs):
        super().teardown_test_environment(**kwargs)
        self._settings_override.disable()
        shutil.rmtree(self._media_root, ignore_errors=True)
