"""Small helpers shared by the characterisation tests.

These tests describe what BizMind does TODAY (Milestone 0). When a later
milestone changes a behaviour on purpose, the matching test should be
changed on purpose too, in the same commit.
"""
import shutil
import tempfile

from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import override_settings

from accounts.models import User
from datasets.models import Dataset

PASSWORD = "strong-password-123"

# Totals: revenue 5500, North 5000 (Laptop), South 500 (Phone).
# Triggers all three sales rules (see decisions/test_characterisation.py).
SALES_CSV = (
    "date,product,region,units_sold,unit_price\n"
    "2024-01-01,Laptop,North,10,500\n"
    "2024-01-02,Phone,South,5,100\n"
)

MARKETING_CSV = (
    "date,campaign,channel,impressions,clicks,conversions,spend,revenue\n"
    "2024-01-01,Summer,Search,1000,50,5,100,150\n"
)

FINANCE_CSV = (
    "date,category,department,amount,type\n"
    "2024-01-01,Sales,Ops,1000,income\n"
    "2024-01-02,Rent,Ops,500,expense\n"
)


class TempMediaMixin:
    """Give every single test its own empty MEDIA_ROOT, deleted afterwards.

    The test runner already keeps tests out of the real ``media/`` folder.
    This goes one step further, so a test that inspects stored files never
    sees files left by a different test. Put it BEFORE TestCase in the bases
    and call ``super().setUp()`` if you define your own setUp.
    """

    def setUp(self):
        super().setUp()
        root = tempfile.mkdtemp(prefix="bizmind-test-media-")
        self.addCleanup(shutil.rmtree, root, True)
        self.enterContext(override_settings(MEDIA_ROOT=root))


class RealCacheMixin:
    """Turn the real (in-memory) cache back on for rate-limit tests.

    The test runner uses a dummy cache so counters never leak between tests.
    Tests that WANT counters use this mixin, which also empties the cache
    before and after every test. Put it BEFORE TestCase in the bases and call
    ``super().setUp()`` if you define your own setUp.
    """

    def setUp(self):
        super().setUp()
        self.enterContext(
            override_settings(
                CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
            )
        )
        cache.clear()
        self.addCleanup(cache.clear)


def make_user(email="analyst@example.com", role="ANALYST", password=PASSWORD):
    user = User.objects.create_user(email=email, password=password)
    user.role = role
    user.save(update_fields=("role",))
    return user


def make_dataset(user, name="Dataset", dataset_type="sales", **extra):
    """Create a Dataset row directly (no CSV, no processing)."""
    return Dataset.objects.create(
        uploaded_by=user,
        name=name,
        type=dataset_type,
        file="",
        **extra,
    )


def csv_upload(text, filename="data.csv"):
    return SimpleUploadedFile(filename, text.encode("utf-8"), content_type="text/csv")


def message_texts(response):
    """Flash messages queued on the response's request."""
    return [str(m) for m in get_messages(response.wsgi_request)]
