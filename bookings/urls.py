from django.urls import path

from . import views

app_name = 'bookings'

urlpatterns = [
    path('mis-reservas/', views.my_bookings, name='my_bookings'),
]
