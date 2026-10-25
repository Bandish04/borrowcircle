from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from .models import Reservation
from .serializers import ReservationSerializer

class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Reservation.objects.filter(models.Q(borrower=self.request.user) | models.Q(item__owner=self.request.user))

    @transaction.atomic
    def perform_create(self, serializer):
        # We will add row-level locking here in the next step when we define the service layer!
        serializer.save(borrower=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def approve(self, request, pk=None):
        reservation = self.get_object()
        if reservation.item.owner != request.user:
            return Response({"error": "Only the owner can approve."}, status=status.HTTP_403_FORBIDDEN)
        
        reservation.status = Reservation.Status.APPROVED
        reservation.save()
        return Response({'status': 'approved'})