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
            qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(location__icontains=query))
        return qs
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    def perform_update(self, serializer):
        if serializer.instance.owner_id != self.request.user.id:
            raise PermissionDenied("Only the owner can edit this listing.")
        serializer.save()
