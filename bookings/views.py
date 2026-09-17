from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from shops.models import BarberProfile, Barbershop, Branch, Service

from .models import Appointment


def _parse_starts_at(date_str, time_str):
    naive = datetime.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M')
    return timezone.make_aware(naive)


@require_http_methods(['GET', 'POST'])
def public_booking(request, slug):
    shop = get_object_or_404(Barbershop, slug=slug, is_active=True)
    branches = shop.branches.filter(is_active=True)
    services = shop.services.filter(is_active=True)
    barbers = shop.barbers.filter(is_active=True).select_related('user')
    cfg = shop.form_config
    error = None

    if request.method == 'POST':
        guest_name = request.POST.get('guest_name', '').strip()
        guest_phone = request.POST.get('guest_phone', '').strip()
        guest_email = request.POST.get('guest_email', '').strip()
        notes = request.POST.get('notes', '').strip()
        branch_id = request.POST.get('branch')
        service_id = request.POST.get('service')
        barber_id = request.POST.get('barber') or None
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')

        if not guest_name:
            error = 'Ingresá tu nombre.'
        elif cfg.get('require_phone') and not guest_phone:
            error = 'Ingresá tu teléfono.'
        elif not branch_id or not service_id or not date_str or not time_str:
            error = 'Completá todos los campos obligatorios.'
        else:
            try:
                branch = branches.get(pk=branch_id)
                service = services.get(pk=service_id)
                barber = None
                if barber_id and cfg.get('show_barber'):
                    barber = barbers.get(pk=barber_id)
                starts_at = _parse_starts_at(date_str, time_str)
                ends_at = starts_at + timedelta(minutes=service.duration_min)

                client = request.user if request.user.is_authenticated else None
                if client and not guest_email and client.email:
                    guest_email = client.email

                appointment = Appointment.objects.create(
                    shop=shop,
                    branch=branch,
                    barber=barber,
                    service=service,
                    client=client,
                    guest_name=guest_name,
                    guest_phone=guest_phone,
                    guest_email=guest_email,
                    starts_at=starts_at,
                    ends_at=ends_at,
                    notes=notes if cfg.get('show_notes') else '',
                    status=Appointment.Status.PENDING,
                    source=Appointment.Source.WEB,
                )
                return redirect(appointment.whatsapp_url())
            except (Branch.DoesNotExist, Service.DoesNotExist, BarberProfile.DoesNotExist, ValueError):
                error = 'Datos inválidos. Revisá el formulario.'

    initial = {
        'guest_name': '',
        'guest_phone': '',
        'guest_email': '',
    }
    if request.user.is_authenticated:
        initial['guest_name'] = request.user.full_name
        initial['guest_phone'] = request.user.phone
        initial['guest_email'] = request.user.email

    return render(request, 'bookings/public_booking.html', {
        'shop': shop,
        'branches': branches,
        'services': services,
        'barbers': barbers,
        'cfg': cfg,
        'error': error,
        'initial': initial,
        'min_date': timezone.localdate().isoformat(),
    })


@login_required
def my_bookings(request):
    appointments = (
        Appointment.objects.filter(client=request.user)
        .select_related('shop', 'branch', 'service', 'barber__user')
        .order_by('-starts_at')
    )
    return render(request, 'bookings/my_bookings.html', {'appointments': appointments})
