from django.urls import path
from rest_framework.routers import DefaultRouter

from .auth_views import ThrottledTokenObtainPairView, ThrottledTokenRefreshView
from .views import (
    DatasetViewSet,
    SalesRecordViewSet,
    MarketingRecordViewSet,
    FinanceRecordViewSet,
    DecisionViewSet,
)


router = DefaultRouter()

# =========================
# API Routes
# =========================
router.register("datasets", DatasetViewSet, basename="dataset")
router.register("sales", SalesRecordViewSet, basename="sales")
router.register("marketing", MarketingRecordViewSet, basename="marketing")
router.register("finance", FinanceRecordViewSet, basename="finance")
router.register("decisions", DecisionViewSet, basename="decision")


urlpatterns = [
    # =========================
    # JWT Authentication
    # =========================
    path(
        "auth/token/",
        ThrottledTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "auth/token/refresh/",
        ThrottledTokenRefreshView.as_view(),
        name="token_refresh",
    ),

    # =========================
    # API Routes
    # =========================
    *router.urls,
]