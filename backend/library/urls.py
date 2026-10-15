from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ItemViewSet, BookingViewSet
router = DefaultRouter()
router.register("categories", CategoryViewSet)
router.register("items", ItemViewSet, basename="item")
router.register("bookings", BookingViewSet, basename="booking")
urlpatterns = router.urls
