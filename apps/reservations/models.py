import uuid
from django.conf import settings
from django.db import models
from apps.items.models import Item

class Reservation(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        CANCELLED = 'cancelled', 'Cancelled'
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        EXPIRED = 'expired', 'Expired'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='reservations')
    borrower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservations')
    
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    message = models.TextField(blank=True, max_length=500)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    idempotency_key = models.UUIDField(unique=True, help_text="Prevents duplicate bookings.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item.title} - {self.borrower.username} ({self.status})"