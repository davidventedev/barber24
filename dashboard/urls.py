from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.home, name='home'),
    path('barbero/', views.barber_home, name='barber_home'),
    path('dueno/', views.owner_home, name='owner_home'),
    path('calendario/', views.calendar_view, name='calendar'),
    path('clientes/', views.clients_view, name='clients'),
    path('metricas/', views.metrics_view, name='metrics'),
    path('reservas/<int:pk>/estado/', views.appointment_status, name='appointment_status'),

    # Settings
    path('config/general/', views.settings_general, name='settings_general'),
    path('config/formulario/', views.settings_form, name='settings_form'),
    path('config/catalogo/', views.settings_catalog, name='settings_catalog'),
    path('config/catalogo/nuevo/', views.service_create, name='service_create'),
    path('config/catalogo/<int:pk>/', views.service_edit, name='service_edit'),
    path('config/sucursales/', views.settings_branches, name='settings_branches'),
    path('config/sucursales/nueva/', views.branch_create, name='branch_create'),
    path('config/sucursales/<int:pk>/', views.branch_edit, name='branch_edit'),
    path('config/barberos/', views.settings_barbers, name='settings_barbers'),
    path('config/barberos/nuevo/', views.barber_create, name='barber_create'),
    path('config/barberos/<int:pk>/', views.barber_edit, name='barber_edit'),

    # Superadmin
    path('superadmin/', views.superadmin_home, name='superadmin'),
    path('superadmin/tiendas/nueva/', views.superadmin_shop_create, name='superadmin_shop_create'),
    path('superadmin/tiendas/<int:pk>/', views.superadmin_shop_edit, name='superadmin_shop_edit'),
    path('superadmin/usuarios/', views.superadmin_users, name='superadmin_users'),
    path('superadmin/usuarios/<int:pk>/toggle/', views.superadmin_user_toggle, name='superadmin_user_toggle'),
]
