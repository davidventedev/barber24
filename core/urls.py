from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('manifest.webmanifest', views.manifest, name='manifest'),
    path('sw.js', views.service_worker, name='sw'),
]
