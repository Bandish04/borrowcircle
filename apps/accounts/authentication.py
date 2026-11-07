
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import User


class CustomJWTAuthentication(JWTAuthentication):

    def get_user(self, validated_token):
        user = super().get_user(validated_token)

        if not user.is_verified:
            raise AuthenticationFailed(
                'Your account email is not verified.',
                code='account_not_verified',
            )

        if user.account_status != User.AccountStatus.ACTIVE:
            raise AuthenticationFailed(
                'Your account is not active. Please contact support.',
                code='account_not_active',
            )

        return user
