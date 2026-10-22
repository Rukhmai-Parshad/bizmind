"""Account erasure (self-service deletion, DPDP Act 2023: right to erasure)."""
from django.contrib.sessions.models import Session
from django.core.files.storage import default_storage
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken


def _delete_sessions(user):
    """Remove every login session that belongs to this user, on any device."""
    for session in Session.objects.filter(expire_date__gt=timezone.now()):
        if session.get_decoded().get("_auth_user_id") == str(user.pk):
            session.delete()


def delete_account(user):
    """Erase the account and everything that belongs to it.

    Deleting the user cascades to its datasets, parsed rows and decisions.
    Refresh-token records and sessions are removed explicitly because they do
    not cascade, and any CSV file still on disk is deleted after the commit.
    """
    leftover_files = list(user.datasets.exclude(file="").values_list("file", flat=True))

    with transaction.atomic():
        OutstandingToken.objects.filter(user=user).delete()  # also removes blacklist rows
        _delete_sessions(user)
        user.delete()
        transaction.on_commit(lambda: [default_storage.delete(name) for name in leftover_files])
