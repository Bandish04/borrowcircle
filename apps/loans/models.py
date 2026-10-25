import uuid
from django.conf import settings
from django.db import models
from apps.reservations.models import Reservation


class Loan(models.Model):
    class Status(models.TextChoices):
        AWAITING_HANDOVER = 'awaiting_handover', 'Awaiting Handover'
        ON_LOAN = 'on_loan', 'On Loan'
        AWAITING_RETURN = 'awaiting_return', 'Awaiting Return'
        RETURNED = 'returned', 'Returned'
        OVERDUE = 'overdue', 'Overdue'
        DISPUTED = 'disputed', 'Disputed'
        CLOSED = 'closed', 'Closed'

    class DepositStatus(models.TextChoices):
        NONE = 'none', 'None'
        HELD = 'held', 'Held'
        RELEASED = 'released', 'Released'
        PARTIALLY_WITHHELD = 'partially_withheld', 'Partially Withheld'
        FORFEITED = 'forfeited', 'Forfeited'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reservation = models.OneToOneField(Reservation, on_delete=models.PROTECT, related_name='loan')
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.AWAITING_HANDOVER)
    deposit_status = models.CharField(max_length=25, choices=DepositStatus.choices, default=DepositStatus.NONE)
    
    agreed_deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    handover_at = models.DateTimeField(null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Loan for {self.reservation.item.title} ({self.status})"


class LoanEvent(models.Model):
    """Append-only historical timeline of every action on a loan."""
    class EventType(models.TextChoices):
        REQUESTED = 'requested', 'Requested'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        CANCELLED = 'cancelled', 'Cancelled'
        HANDOVER_CONFIRMED = 'handover_confirmed', 'Handover Confirmed'
        RETURN_CONFIRMED = 'return_confirmed', 'Return Confirmed'
        OVERDUE_FLAGGED = 'overdue_flagged', 'Overdue Flagged'
        DISPUTE_OPENED = 'dispute_opened', 'Dispute Opened'
        DISPUTE_RESOLVED = 'dispute_resolved', 'Dispute Resolved'
        DEPOSIT_CHANGED = 'deposit_changed', 'Deposit Changed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='events')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    event_type = models.CharField(max_length=30, choices=EventType.choices)
    note = models.TextField(blank=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.event_type} on {self.loan.id} at {self.created_at}"


class ConditionReport(models.Model):
    class Stage(models.TextChoices):
        HANDOVER = 'handover', 'Handover'
        RETURN = 'return', 'Return'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='condition_reports')
    stage = models.CharField(max_length=15, choices=Stage.choices)
    
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    condition_rating = models.PositiveSmallIntegerField(help_text="Rating 1 (damaged) to 5 (excellent)")
    notes = models.TextField(blank=True, max_length=1000)
    
    owner_confirmed = models.BooleanField(default=False)
    borrower_confirmed = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False, help_text="Locks once both parties confirm.")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('loan', 'stage', 'reported_by')

    def __str__(self):
        return f"{self.stage.capitalize()} report for {self.loan.id} by {self.reported_by.username}"


class ConditionPhoto(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(ConditionReport, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='condition_photos/')
    created_at = models.DateTimeField(auto_now_add=True)


class LedgerEntry(models.Model):
    """Append-only deposit ledger tracking security deposits."""
    class EntryType(models.TextChoices):
        DEPOSIT_HOLD = 'deposit_hold', 'Deposit Hold'
        DEPOSIT_RELEASE = 'deposit_release', 'Deposit Release'
        DEPOSIT_WITHHOLD = 'deposit_withhold', 'Deposit Withhold'
        ADJUSTMENT = 'adjustment', 'Adjustment'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='ledger_entries')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    entry_type = models.CharField(max_length=25, choices=EntryType.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.TextField(blank=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']