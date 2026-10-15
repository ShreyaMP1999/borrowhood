from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q, F

class Category(models.Model):
    name = models.CharField(max_length=60, unique=True)
    def __str__(self): return self.name

class Item(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="items")
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    title = models.CharField(max_length=120)
    description = models.TextField()
    condition = models.CharField(max_length=20, choices=[(x, x.title()) for x in ["new", "good", "fair"]], default="good")
    location = models.CharField(max_length=120)
    image = models.ImageField(upload_to="items/", blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-created_at"]
    def __str__(self): return self.title

class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending"
        APPROVED = "approved"
        DECLINED = "declined"
        COLLECTED = "collected"
        RETURNED = "returned"
        CANCELLED = "cancelled"
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="bookings")
    borrower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bookings")
    start_date = models.DateField()
    end_date = models.DateField()
    message = models.TextField(blank=True, max_length=1000)
    return_notes = models.TextField(blank=True, max_length=1000)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-created_at"]
        constraints = [models.CheckConstraint(condition=Q(end_date__gte=F("start_date")), name="booking_valid_dates")]
        indexes = [models.Index(fields=["item", "status", "start_date", "end_date"])]

class Review(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="review")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.CheckConstraint(condition=Q(rating__gte=1, rating__lte=5), name="review_rating_range")]
