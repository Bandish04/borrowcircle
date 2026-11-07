
from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView

from .serializers import CustomTokenRefreshSerializer
from .views import (
    RegisterView,
    CustomTokenObtainPairView,
    UserDetailView,
    LogoutView,
    VerifyEmailView,
    ResendOTPView,
    ForgotPasswordView,
    VerifyResetCodeView,
    ResetPasswordView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='auth-login'),
    path(
        'refresh/',
        TokenRefreshView.as_view(
            serializer_class=CustomTokenRefreshSerializer
        ),
        name='auth-token-refresh',
    ),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('me/', UserDetailView.as_view(), name='user-detail'),
    path('verify-email/', VerifyEmailView.as_view(), name='auth-verify-email'),
    path('resend-otp/', ResendOTPView.as_view(), name='auth-resend-otp'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='auth-forgot-password'),
    path('verify-reset-code/', VerifyResetCodeView.as_view(), name='auth-verify-reset-code'),
    path('reset-password/', ResetPasswordView.as_view(), name='auth-reset-password'),
]
