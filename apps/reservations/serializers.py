from rest_framework import serializers
from .models import Reservation

class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ('id', 'item', 'start_at', 'end_at', 'message', 'status', 'idempotency_key')
        read_only_fields = ('id', 'status')

    def validate(self, data):
        if data['start_at'] >= data['end_at']:
            raise serializers.ValidationError("End time must be after start time.")
        return data