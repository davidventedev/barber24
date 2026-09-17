from django.contrib import admin

from .models import BarberProfile, Barbershop, Branch, Service


class BranchInline(admin.TabularInline):
    model = Branch
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
    inlines = [BranchInline, ServiceInline]


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'shop', 'whatsapp_number', 'is_active']
    list_filter = ['shop', 'is_active']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'shop', 'duration_min', 'price', 'is_active']
    list_filter = ['shop', 'is_active']


@admin.register(BarberProfile)
class BarberProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'shop', 'branch', 'is_active']
    list_filter = ['shop', 'is_active']
