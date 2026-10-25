from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from django.utils import timezone
from .models import Loan, LoanEvent, ConditionReport
from .serializers import LoanSerializer, ConditionReportSerializer


class LoanViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LoanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Loan.objects.filter(
            Q(reservation__borrower=user) | Q(reservation__item__owner=user)
        )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def confirm_handover(self, request, pk=None):
        loan = self.get_object()
        user = request.user
        
        if user not in [loan.reservation.borrower, loan.reservation.item.owner]:
            return Response({"error": "Not a participant in this loan."}, status=status.HTTP_403_FORBIDDEN)

        if loan.status != Loan.Status.AWAITING_HANDOVER:
            return Response({"error": "Loan is not awaiting handover."}, status=status.HTTP_400_BAD_REQUEST)

        # Get or create condition report for handover
        report, _ = ConditionReport.objects.get_or_create(
            loan=loan,
            stage=ConditionReport.Stage.HANDOVER,
            reported_by=user,
            defaults={'condition_rating': request.data.get('condition_rating', 5), 'notes': request.data.get('notes', '')}
        )

        if user == loan.reservation.item.owner:
            report.owner_confirmed = True
        else:
            report.borrower_confirmed = True

        report.save()

        # Check if both owner and borrower confirmed handover
        all_handover_reports = ConditionReport.objects.filter(loan=loan, stage=ConditionReport.Stage.HANDOVER)
        owner_ok = all_handover_reports.filter(owner_confirmed=True).exists()
        borrower_ok = all_handover_reports.filter(borrower_confirmed=True).exists()

        if owner_ok and borrower_ok:
            loan.status = Loan.Status.ON_LOAN
            loan.handover_at = timezone.now()
            loan.save()

            # Record event log
            LoanEvent.objects.create(
                loan=loan,
                actor=user,
                event_type=LoanEvent.EventType.HANDOVER_CONFIRMED,
                note="Handover confirmed by both parties."
            )

        return Response({'status': loan.status, 'detail': 'Handover confirmation recorded.'})