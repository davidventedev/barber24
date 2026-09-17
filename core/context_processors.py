from django.conf import settings


def branding(request):
    return {
        'BRAND_NAME': getattr(settings, 'BRAND_NAME', 'Barber24'),
        'BRAND_PRIMARY': getattr(settings, 'BRAND_PRIMARY', '#EAC452'),
    }
