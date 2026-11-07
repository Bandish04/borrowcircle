from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import User, Profile, ReliabilitySummary
from rest_framework.exceptions import AuthenticationFailed

from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('bio', 'city', 'phone_number', 'avatar', 'created_at', 'updated_at')


class ReliabilitySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReliabilitySummary
        fields = ('completed_loans', 'on_time_returns', 'late_returns', 'cancellations')


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=10)
    profile = ProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'password', 'role', 'is_verified', 'profile')
        read_only_fields = ('id', 'role', 'is_verified')

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        password = validated_data.pop('password')

        user = User.objects.create_user(
            password=password,
            **validated_data
        )

        # Create Profile and Reliability Summary automatically.
        Profile.objects.create(user=user, **profile_data)
        ReliabilitySummary.objects.create(user=user)

        return user

class UserDetailSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    reliability = ReliabilitySummarySerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'role', 'account_status', 'is_verified', 'profile', 'reliability', 'date_joined')
        read_only_fields = ('id', 'email', 'role', 'account_status', 'is_verified', 'date_joined')


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)

        if not self.user.is_verified:
            raise AuthenticationFailed(
                'Please verify your email address before logging in.'
            )

        if self.user.account_status != User.AccountStatus.ACTIVE:
            raise AuthenticationFailed(
                'Your account is not active. Please contact support.'
            )

        return data



class CustomTokenRefreshSerializer(TokenRefreshSerializer):

    def validate(self, attrs):
        refresh = RefreshToken(attrs['refresh'])

        user_id = refresh.get('user_id')
        user = User.objects.filter(pk=user_id).first()

        if (
            not user
            or not user.is_verified
            or user.account_status != User.AccountStatus.ACTIVE
        ):
            raise AuthenticationFailed(
                'Your account is not active or verified. Please contact support.'
            )

        return super().validate(attrs)