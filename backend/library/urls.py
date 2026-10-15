from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ItemViewSet, BookingViewSet, ReviewViewSet, dashboard
router = DefaultRouter()
router.register("categories", CategoryViewSet)
router.register("items", ItemViewSet, basename="item")
router.register("bookings", BookingViewSet, basename="booking")
router.register("reviews", ReviewViewSet, basename="review")
urlpatterns = [path("dashboard/", dashboard)] + router.urls
