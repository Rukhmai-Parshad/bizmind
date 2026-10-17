from django.contrib import admin
from django.urls import include, path

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerSplitView,
)


urlpatterns = [
    # =========================
    # OpenAPI Schema
    # =========================
    path(
        "api/schema/",
        SpectacularAPIView.as_view(),
        name="schema",
    ),

    # =========================
    # Swagger UI
    # =========================
    path(
        "api/docs/",
        SpectacularSwaggerSplitView.as_view(url_name="schema"),
        name="swagger-ui",
    ),

    # =========================
    # Admin
    # =========================
    path("admin/", admin.site.urls),

    # =========================
    # API
    # =========================
    path("api/", include("api.urls")),

    # =========================
    # Application URLs
    # =========================
    path("", include("core.urls")),
    path("accounts/", include("accounts.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("datasets/", include("datasets.urls")),
    path("decisions/", include("decisions.urls")),
]