from django.contrib import admin
from .models import Category, Item, Booking, Review

admin.site.register([Category, Item, Booking, Review])
