from django.contrib import admin

from .models import BarberProfile, Barbershop, Establishment, Service


class EstablishmentInline(admin.TabularInline):
    model = Establishment
    extra = 0


class ServiceInline(admin.TabularInline):
    model = Service
    extra = 0


@admin.register(Barbershop)
class BarbershopAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'city', 'is_active', 'created_at']
    list_filter = ['is_active', 'city']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [EstablishmentInline, ServiceInline]


@admin.register(Establishment)
class EstablishmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'shop', 'open_time', 'close_time', 'whatsapp_number', 'is_active']
    list_filter = ['shop', 'is_active']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'shop', 'duration_min', 'price', 'is_active']
    list_filter = ['shop', 'is_active']


@admin.register(BarberProfile)
class BarberProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'shop', 'establishment', 'is_active']
    list_filter = ['shop', 'is_active']
    fields = [
        'user', 'shop', 'establishment', 'photo', 'bio', 'specialties',
        'calendar_color', 'work_hours', 'is_active',
    ]
