from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .throttles import AuthAccountRateThrottle, AuthIPRateThrottle


class ThrottledTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [AuthIPRateThrottle, AuthAccountRateThrottle]


class ThrottledTokenRefreshView(TokenRefreshView):
    throttle_classes = [AuthIPRateThrottle]
