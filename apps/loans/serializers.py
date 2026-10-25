from rest_framework import serializers
from .models import Loan, LoanEvent, ConditionReport, ConditionPhoto, LedgerEntry


class ConditionPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConditionPhoto
        fields = ('id', 'image', 'created_at')


class ConditionReportSerializer(serializers.ModelSerializer):
    photos = ConditionPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = ConditionReport
        fields = (
            'id', 'loan', 'stage', 'reported_by', 'condition_rating',
            'notes', 'owner_confirmed', 'borrower_confirmed', 'is_locked', 'photos', 'created_at'
        )
        read_only_fields = ('id', 'reported_by', 'owner_confirmed', 'borrower_confirmed', 'is_locked', 'created_at')


class LoanEventSerializer(serializers.ModelSerializer):
    actor_username = serializers.ReadOnlyField(source='actor.username')

    class Meta:
        model = LoanEvent
        fields = ('id', 'event_type', 'actor_username', 'note', 'created_at')


class LedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = ('id', 'entry_type', 'amount', 'note', 'created_at')


class LoanSerializer(serializers.ModelSerializer):
    events = LoanEventSerializer(many=True, read_only=True)
    condition_reports = ConditionReportSerializer(many=True, read_only=True)
    ledger_entries = LedgerEntrySerializer(many=True, read_only=True)

    class Meta:
        model = Loan
        fields = (
            'id', 'reservation', 'status', 'deposit_status', 'agreed_deposit_amount',
            'handover_at', 'returned_at', 'events', 'condition_reports', 'ledger_entries', 'created_at'
        )
        read_only_fields = ('id', 'status', 'deposit_status', 'created_at')