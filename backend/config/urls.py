from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from library import accounts

urlpatterns = [
    path("api/", include("library.urls")),
    path("admin/", admin.site.urls),
    path("api/auth/register/", accounts.register),
    path("api/auth/login/", accounts.login),
    path("api/auth/me/", accounts.me),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
