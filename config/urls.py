from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from bookings.views import public_booking

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),
    path('app/', include('dashboard.urls')),
    path('reservas/', include('bookings.urls')),
    path('b/<slug:slug>/', public_booking, name='public_booking'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
