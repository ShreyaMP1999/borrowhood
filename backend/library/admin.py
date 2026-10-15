from django.contrib import admin
from .models import Category, Item, Booking, Review

admin.site.register([Category, Item, Review])


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["item", "borrower", "start_date", "end_date", "status"]
    list_filter = ["status"]
    readonly_fields = [field.name for field in Booking._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
