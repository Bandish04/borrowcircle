from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'title', 'message', 'delivery_status', 'is_read', 'created_at')
        read_only_fields = ('id', 'title', 'message', 'delivery_status', 'created_at')