from rest_framework import serializers
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    reviewer_username = serializers.ReadOnlyField(source='reviewer.username')
    reviewee_username = serializers.ReadOnlyField(source='reviewee.username')

    class Meta:
        model = Review
        fields = ('id', 'loan', 'reviewer', 'reviewer_username', 'reviewee', 'reviewee_username', 'rating', 'comment', 'created_at')
        read_only_fields = ('id', 'reviewer', 'reviewer_username', 'reviewee_username', 'created_at')

    def validate(self, data):
        loan = data['loan']
        request_user = self.context['request'].user
        
        # Verify user is a participant
        borrower = loan.reservation.borrower
        owner = loan.reservation.item.owner
        
        if request_user not in [borrower, owner]:
            raise serializers.ValidationError("You are not a participant in this loan.")
            
        # Verify loan is returned
        if loan.status not in ['returned', 'closed']:
            raise serializers.ValidationError("Reviews are only allowed after a loan has been returned.")
            
        return data

    def create(self, validated_data):
        loan = validated_data['loan']
        request_user = self.context['request'].user
        
        # Determine who the reviewee is
        borrower = loan.reservation.borrower
        owner = loan.reservation.item.owner
        reviewee = owner if request_user == borrower else borrower

        validated_data['reviewer'] = request_user
        validated_data['reviewee'] = reviewee
        return super().create(validated_data)