from rest_framework import serializers
from .models import Dispute, DisputeEvidence


class DisputeEvidenceSerializer(serializers.ModelSerializer):
    uploaded_by_username = serializers.ReadOnlyField(source='uploaded_by.username')

    class Meta:
        model = DisputeEvidence
        fields = ('id', 'dispute', 'uploaded_by', 'uploaded_by_username', 'image', 'note', 'created_at')
        read_only_fields = ('id', 'uploaded_by', 'uploaded_by_username', 'created_at')

    def create(self, validated_data):
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)


class DisputeSerializer(serializers.ModelSerializer):
    evidence = DisputeEvidenceSerializer(many=True, read_only=True)
    opened_by_username = serializers.ReadOnlyField(source='opened_by.username')

    class Meta:
        model = Dispute
        fields = (
            'id', 'loan', 'opened_by', 'opened_by_username', 'reason',
            'description', 'status', 'resolution_notes', 'resolved_by', 'evidence', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'opened_by', 'opened_by_username', 'status', 'resolution_notes', 'resolved_by', 'created_at', 'updated_at')

    def create(self, validated_data):
        validated_data['opened_by'] = self.context['request'].user
        return super().create(validated_data)