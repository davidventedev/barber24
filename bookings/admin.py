from django.contrib import admin

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['guest_name', 'shop', 'service', 'starts_at', 'status', 'source']
    list_filter = ['status', 'shop', 'source']
    search_fields = ['guest_name', 'guest_phone', 'guest_email']
    date_hierarchy = 'starts_at'
