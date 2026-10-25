from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import User, Profile, ReliabilitySummary


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

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        password = validated_data.pop('password')
        
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        # Create Profile and Reliability Summary automatically
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