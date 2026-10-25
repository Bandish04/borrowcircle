from rest_framework import serializers
from .models import Category, Item, ItemPhoto, MaintenanceWindow


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'parent')


class ItemPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemPhoto
        fields = ('id', 'image', 'is_cover', 'created_at')


class MaintenanceWindowSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceWindow
        fields = ('id', 'start_at', 'end_at', 'reason')


class ItemSerializer(serializers.ModelSerializer):
    photos = ItemPhotoSerializer(many=True, read_only=True)
    owner_username = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Item
        fields = (
            'id', 'owner', 'owner_username', 'category', 'title', 'description',
            'condition', 'status', 'deposit_amount', 'max_loan_days',
            'buffer_hours', 'pickup_area', 'photos', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'owner', 'created_at', 'updated_at')

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)