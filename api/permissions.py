from rest_framework.permissions import SAFE_METHODS, BasePermission

from datasets.validators import can_upload


class AdminOrAnalystForWrites(BasePermission):
    """Anyone logged in may read; only ADMIN/ANALYST may create, change or delete.

    Uses the same ``can_upload`` rule as the web upload view, so a VIEWER is
    refused with HTTP 403 in both places (audit S1).
    """

    message = "Your account has read-only access."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return can_upload(request.user)
