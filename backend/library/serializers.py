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

class BookingSerializer(serializers.ModelSerializer):
    item_title = serializers.CharField(source="item.title", read_only=True)
    owner = serializers.IntegerField(source="item.owner_id", read_only=True)
    borrower_name = serializers.CharField(source="borrower.username", read_only=True)
    reviewed = serializers.SerializerMethodField()
    def get_reviewed(self, obj): return hasattr(obj, "review")
    class Meta:
        model = Booking
        fields = ["id", "item", "item_title", "owner", "borrower", "borrower_name", "start_date", "end_date", "message", "status", "return_notes", "reviewed", "created_at"]
        read_only_fields = ["borrower", "status", "return_notes", "created_at"]
    def validate(self, attrs):
        from django.utils import timezone
        item = attrs["item"]
        if not item.active:
            raise serializers.ValidationError("This item is unavailable.")
        if item.owner_id == self.context["request"].user.id:
            raise serializers.ValidationError("You cannot borrow your own item.")
        if attrs["start_date"] < timezone.localdate() or attrs["end_date"] < attrs["start_date"]:
            raise serializers.ValidationError("Choose a valid date range starting today or later.")
        return attrs

class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="booking.borrower.username", read_only=True)
    item_title = serializers.CharField(source="booking.item.title", read_only=True)
    class Meta:
        model = Review
        fields = ["id", "booking", "rating", "comment", "author", "item_title", "created_at"]
        read_only_fields = ["created_at"]
    def validate_booking(self, booking):
        if booking.borrower_id != self.context["request"].user.id:
            raise serializers.ValidationError("Only the borrower can review this booking.")
        if booking.status != Booking.Status.RETURNED:
            raise serializers.ValidationError("Return the item before leaving a review.")
        return booking
