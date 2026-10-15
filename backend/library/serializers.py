from rest_framework import serializers
from .models import Category, Item, Booking, Review

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]

class ItemSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source="owner.username", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    class Meta:
        model = Item
        fields = ["id", "owner", "owner_name", "category", "category_name", "title", "description", "condition", "location", "image", "active", "created_at"]
        read_only_fields = ["owner", "created_at"]
    def validate_image(self, image):
        if image and image.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Images must be under 5 MB.")
        return image
