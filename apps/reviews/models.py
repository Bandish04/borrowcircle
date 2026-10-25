import uuid
from django.conf import settings
from django.db import models
from apps.loans.models import Loan


class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_given')
    reviewee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_received')
    
    rating = models.PositiveSmallIntegerField(help_text="Rating from 1 to 5")
    comment = models.TextField(blank=True, max_length=1000)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('loan', 'reviewer')  # Only one review per person per loan

    def __str__(self):
        return f"Review ({self.rating}/5) by {self.reviewer.username} for {self.reviewee.username}"