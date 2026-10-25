from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from .models import Dispute, DisputeEvidence, AuditLog
from .serializers import DisputeSerializer, DisputeEvidenceSerializer


class DisputeViewSet(viewsets.ModelViewSet):
    serializer_class = DisputeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'moderator']:
            return Dispute.objects.all()
        return Dispute.objects.filter(Q(opened_by=user) | Q(loan__reservation__borrower=user) | Q(loan__reservation__item__owner=user))

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def resolve(self, request, pk=None):
        user = request.user
        if user.role not in ['admin', 'moderator']:
            return Response({"error": "Only staff can resolve disputes."}, status=status.HTTP_403_FORBIDDEN)

        dispute = self.get_object()
        dispute.status = Dispute.Status.RESOLVED
        dispute.resolution_notes = request.data.get('resolution_notes', '')
        dispute.resolved_by = user
        dispute.save()

        # Audit log entry
        AuditLog.objects.create(
            actor=user,
            action="RESOLVE_DISPUTE",
            target_object=f"Dispute {dispute.id}",
            notes=dispute.resolution_notes
        )

        return Response({'status': 'resolved'})


class DisputeEvidenceViewSet(viewsets.ModelViewSet):
    serializer_class = DisputeEvidenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DisputeEvidence.objects.filter(
            Q(dispute__opened_by=self.request.user) | Q(dispute__loan__reservation__borrower=self.request.user) | Q(dispute__loan__reservation__item__owner=self.request.user)
        )