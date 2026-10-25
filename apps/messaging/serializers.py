from rest_framework import serializers
from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.ReadOnlyField(source='sender.username')

    class Meta:
        model = Message
        fields = ('id', 'conversation', 'sender', 'sender_username', 'body', 'is_read', 'created_at')
        read_only_fields = ('id', 'sender', 'sender_username', 'is_read', 'created_at')

    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    participant_one_username = serializers.ReadOnlyField(source='participant_one.username')
    participant_two_username = serializers.ReadOnlyField(source='participant_two.username')

    class Meta:
        model = Conversation
        fields = ('id', 'reservation', 'participant_one', 'participant_one_username', 'participant_two', 'participant_two_username', 'messages', 'created_at')
        read_only_fields = ('id', 'participant_one', 'participant_two', 'created_at')