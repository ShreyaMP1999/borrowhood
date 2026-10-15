from django.db.models import Q
from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from .models import Category, Item
from .serializers import CategorySerializer, ItemSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.order_by("name")
    serializer_class = CategorySerializer
    pagination_class = None


class ItemViewSet(viewsets.ModelViewSet):
    serializer_class = ItemSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        qs = Item.objects.select_related("owner", "category")
        if self.request.query_params.get("mine") == "1":
            if not self.request.user.is_authenticated:
                return qs.none()
            qs = qs.filter(owner=self.request.user)
        else:
            qs = qs.filter(active=True)
        if category := self.request.query_params.get("category"):
            qs = qs.filter(category_id=category) if category.isdigit() else qs.none()
        if query := self.request.query_params.get("search"):
            qs = qs.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(location__icontains=query)
            )
        return qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.owner_id != self.request.user.id:
            raise PermissionDenied("Only the owner can edit this listing.")
        serializer.save()


from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Booking
from .serializers import BookingSerializer
from .services import transition


class BookingViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(
            Q(borrower=self.request.user) | Q(item__owner=self.request.user)
        ).select_related("item", "borrower", "review")

    def perform_create(self, serializer):
        serializer.save(borrower=self.request.user)

    @action(detail=True, methods=["post"], url_path="transition")
    def change_status(self, request, pk=None):
        booking = self.get_object()
        notes = request.data.get("return_notes", "")
        if not isinstance(notes, str):
            from rest_framework.exceptions import ValidationError

            raise ValidationError("Return notes must be text.")
        updated = transition(
            booking.pk, request.user, request.data.get("action", ""), notes
        )
        return Response(self.get_serializer(updated).data)


from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from .models import Review
from .serializers import ReviewSerializer


class ReviewViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        qs = Review.objects.select_related(
            "booking__borrower", "booking__item"
        ).order_by("-created_at")
        item = self.request.query_params.get("item")
        if item:
            qs = qs.filter(booking__item_id=item) if item.isdigit() else qs.none()
        return qs


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def dashboard(request):
    mine = Booking.objects.filter(
        Q(borrower=request.user) | Q(item__owner=request.user)
    )
    return Response(
        {
            "items_shared": Item.objects.filter(
                owner=request.user, active=True
            ).count(),
            "pending_requests": mine.filter(
                item__owner=request.user, status="pending"
            ).count(),
            "active_loans": mine.filter(status__in=["approved", "collected"]).count(),
            "overdue": mine.filter(
                status="collected", end_date__lt=timezone.localdate()
            ).count(),
            "completed": mine.filter(status="returned").count(),
        }
    )
