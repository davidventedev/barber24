from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.formats import date_format
from django.views.decorators.http import require_http_methods

from accounts.decorators import role_required, shop_required
from accounts.forms import OwnerCreateUserForm, ProfileForm
from bookings.models import Appointment
from shops.forms import (
    BarberProfileForm,
    BarberWorkHoursForm,
    BookingFormConfigForm,
    EstablishmentForm,
    ServiceForm,
    ShopGeneralForm,
)
from shops.models import (
    DEFAULT_CLOSE_TIME,
    DEFAULT_OPEN_TIME,
    BarberProfile,
    Barbershop,
    Establishment,
    Service,
)
User = get_user_model()


def _shop_for(user, shop_id=None):
    if user.is_superadmin_role and shop_id:
        return get_object_or_404(Barbershop, pk=shop_id)
    return user.shop


def _metrics_for_queryset(qs):
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    completed = qs.filter(status=Appointment.Status.COMPLETED)
    month_qs = qs.filter(starts_at__gte=month_start)
    revenue = completed.aggregate(total=Sum('service__price'))['total'] or Decimal('0')
    month_revenue = completed.filter(starts_at__gte=month_start).aggregate(
        total=Sum('service__price')
    )['total'] or Decimal('0')
    return {
        'total': qs.count(),
        'upcoming': qs.filter(
            starts_at__gte=now,
            status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED],
        ).count(),
        'completed': completed.count(),
        'cancelled': qs.filter(status=Appointment.Status.CANCELLED).count(),
        'month_count': month_qs.count(),
        'revenue': revenue,
        'month_revenue': month_revenue,
    }


@login_required
def home(request):
    user = request.user
    if user.is_superadmin_role:
        return redirect('dashboard:superadmin')
    if user.is_client:
        return redirect('bookings:my_bookings')
    if user.is_owner:
        return redirect('dashboard:owner_home')
    if user.is_barber:
        return redirect('dashboard:barber_home')
    return redirect('core:landing')


@role_required(User.Role.BARBER, User.Role.OWNER)
@shop_required
def barber_home(request):
    shop = request.user.shop
    profile = getattr(request.user, 'barber_profile', None)
    qs = Appointment.objects.filter(shop=shop).select_related('service', 'establishment', 'client')
    if request.user.is_barber and profile:
        qs = qs.filter(barber=profile)
    metrics = _metrics_for_queryset(qs)
    upcoming = qs.filter(
        starts_at__gte=timezone.now(),
        status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED],
    ).order_by('starts_at')[:8]
    return render(request, 'dashboard/barber_home.html', {
        'metrics': metrics,
        'upcoming': upcoming,
        'profile': profile,
    })


@role_required(User.Role.OWNER)
@shop_required
def owner_home(request):
    shop = request.user.shop
    qs = Appointment.objects.filter(shop=shop)
    metrics = _metrics_for_queryset(qs)
    barber_stats = (
        BarberProfile.objects.filter(shop=shop, is_active=True)
        .annotate(
            appt_count=Count('appointments'),
            completed=Count('appointments', filter=Q(appointments__status=Appointment.Status.COMPLETED)),
        )
        .select_related('user')
    )
    recent = qs.select_related('service', 'establishment', 'barber__user').order_by('-created_at')[:8]
    return render(request, 'dashboard/owner_home.html', {
        'shop': shop,
        'metrics': metrics,
        'barber_stats': barber_stats,
        'recent': recent,
    })


def _minutes_from_midnight(value):
    return value.hour * 60 + value.minute


def _calendar_layout(appointment, px_per_hour):
    """Position an appointment using exact start time and duration."""
    local_start = timezone.localtime(appointment.starts_at)
    local_end = timezone.localtime(appointment.ends_at)
    start_min = _minutes_from_midnight(local_start)
    duration_min = (local_end - local_start).total_seconds() / 60
    if duration_min <= 0:
        duration_min = appointment.service.duration_min or 30
    # Keep the block within the current day grid.
    duration_min = min(duration_min, (24 * 60) - start_min)
    color = (
        appointment.barber.calendar_color
        if appointment.barber and appointment.barber.calendar_color
        else '#EAC452'
    )
    top = (start_min / 60) * px_per_hour
    height = (duration_min / 60) * px_per_hour
    return {
        'appt': appointment,
        # Format with dot so CSS works under es-ar locale.
        'top': f'{top:.2f}',
        'height': f'{height:.2f}',
        'color': color,
        'start_label': local_start.strftime('%H:%M'),
        'end_label': local_end.strftime('%H:%M'),
        'duration_min': int(round(duration_min)),
    }


def _closed_ranges(open_intervals, px_per_hour):
    """Unavailable bands outside one or more working intervals (full 24h grid)."""
    day_px = 24 * px_per_hour
    if not open_intervals:
        return [{'top': '0.00', 'height': f'{day_px:.2f}'}]

    minutes = []
    for open_time, close_time in open_intervals:
        open_min = _minutes_from_midnight(open_time)
        close_min = _minutes_from_midnight(close_time)
        if close_min > open_min:
            minutes.append([open_min, close_min])
    if not minutes:
        return [{'top': '0.00', 'height': f'{day_px:.2f}'}]

    minutes.sort()
    merged = [minutes[0]]
    for open_min, close_min in minutes[1:]:
        if open_min <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], close_min)
        else:
            merged.append([open_min, close_min])

    ranges = []
    cursor = 0
    for open_min, close_min in merged:
        if open_min > cursor:
            top = (cursor / 60) * px_per_hour
            height = ((open_min - cursor) / 60) * px_per_hour
            ranges.append({'top': f'{top:.2f}', 'height': f'{height:.2f}'})
        cursor = close_min
    if cursor < 24 * 60:
        top = (cursor / 60) * px_per_hour
        ranges.append({'top': f'{top:.2f}', 'height': f'{day_px - top:.2f}'})
    return ranges


def _hours_for_calendar_day(weekday, establishment, barber_profile=None):
    """Effective open intervals for a day, optionally intersecting barber schedule."""
    if establishment:
        est_open, est_close = establishment.open_time, establishment.close_time
    else:
        est_open, est_close = DEFAULT_OPEN_TIME, DEFAULT_CLOSE_TIME

    if not barber_profile:
        if est_close <= est_open:
            return []
        return [(est_open, est_close)]

    return barber_profile.hours_for_weekday(weekday)


@role_required(User.Role.BARBER, User.Role.OWNER)
@shop_required
def calendar_view(request):
    shop = request.user.shop
    profile = getattr(request.user, 'barber_profile', None)
    view_mode = request.GET.get('view', 'week')
    if view_mode not in ('week', 'day'):
        view_mode = 'week'

    week_offset = int(request.GET.get('w', 0) or 0)
    today = timezone.localdate()
    # Sunday-first week: Sun=0 … Sat=6
    today_sun_index = today.isoweekday() % 7
    start = today - timedelta(days=today_sun_index) + timedelta(weeks=week_offset)
    end = start + timedelta(days=7)

    try:
        day_index = int(request.GET.get('d', today_sun_index if week_offset == 0 else 0))
    except (TypeError, ValueError):
        day_index = 0
    day_index = max(0, min(6, day_index))

    barbers = list(
        BarberProfile.objects.filter(shop=shop, is_active=True)
        .select_related('user', 'establishment')
        .order_by('user__first_name', 'user__last_name', 'user__email')
    )

    selected_barber = None
    if request.user.is_barber and profile:
        selected_barber = profile
        barbers = [b for b in barbers if b.pk == profile.pk] or [profile]
    else:
        barber_id = request.GET.get('barber')
        if barber_id:
            selected_barber = next((b for b in barbers if str(b.pk) == str(barber_id)), None)
        if selected_barber is None and barbers:
            selected_barber = barbers[0]

    qs = Appointment.objects.filter(
        shop=shop,
        starts_at__date__gte=start,
        starts_at__date__lt=end,
    ).exclude(status=Appointment.Status.CANCELLED).select_related(
        'service', 'barber__user', 'establishment'
    ).order_by('starts_at')
    if selected_barber:
        qs = qs.filter(barber=selected_barber)

    appointments = list(qs)
    px_per_hour = 96
    hours = list(range(24))
    grid_height = 24 * px_per_hour

    schedule_barber = selected_barber
    selected_establishment = selected_barber.establishment if selected_barber else None

    if selected_establishment:
        open_time = selected_establishment.open_time
        close_time = selected_establishment.close_time
    else:
        open_time = DEFAULT_OPEN_TIME
        close_time = DEFAULT_CLOSE_TIME

    open_top = (_minutes_from_midnight(open_time) / 60) * px_per_hour
    # closed_hours for gutter labels: union of unavailable hours across the week
    closed_hours = set(hours)
    for i in range(7):
        intervals = _hours_for_calendar_day(i, selected_establishment, schedule_barber)
        if not intervals:
            continue
        for day_open, day_close in intervals:
            open_min = _minutes_from_midnight(day_open)
            close_min = _minutes_from_midnight(day_close)
            for h in hours:
                if not (((h + 1) * 60) <= open_min or (h * 60) >= close_min):
                    closed_hours.discard(h)

    now = timezone.localtime()
    show_now = start <= now.date() < end
    now_top = f'{(_minutes_from_midnight(now) / 60) * px_per_hour:.2f}' if show_now else None

    days = []
    for i in range(7):
        day = start + timedelta(days=i)
        day_appts = [a for a in appointments if timezone.localtime(a.starts_at).date() == day]
        intervals = _hours_for_calendar_day(i, selected_establishment, schedule_barber)
        days.append({
            'date': day,
            'index': i,
            'is_today': day == today,
            'is_selected': i == day_index,
            'items': [_calendar_layout(a, px_per_hour) for a in day_appts],
            'count': len(day_appts),
            'closed_ranges': _closed_ranges(intervals, px_per_hour),
            'is_off': not intervals,
        })

    selected_day = days[day_index]
    if view_mode == 'day':
        d = selected_day['date']
        month_label = f'{d.day} {date_format(d, "b").capitalize()} {d.year}'
    else:
        last = end - timedelta(days=1)
        if start.month == last.month:
            month_label = f'{date_format(start, "F")} {start.year}'.capitalize()
        else:
            month_label = (
                f'{date_format(start, "b").capitalize()} – '
                f'{date_format(last, "b").capitalize()} {last.year}'
            )

    def _shift_day(delta):
        idx = day_index + delta
        w = week_offset
        if idx < 0:
            return w - 1, 6
        if idx > 6:
            return w + 1, 0
        return w, idx

    prev_day_w, prev_day_d = _shift_day(-1)
    next_day_w, next_day_d = _shift_day(1)
    barber_q = f'&barber={selected_barber.pk}' if selected_barber else ''

    return render(request, 'dashboard/calendar.html', {
        'days': days,
        'selected_day': selected_day,
        'start': start,
        'end': end - timedelta(days=1),
        'today': today,
        'week_offset': week_offset,
        'prev_w': week_offset - 1,
        'next_w': week_offset + 1,
        'prev_day_w': prev_day_w,
        'prev_day_d': prev_day_d,
        'next_day_w': next_day_w,
        'next_day_d': next_day_d,
        'barber_q': barber_q,
        'view_mode': view_mode,
        'day_index': day_index,
        'hours': hours,
        'closed_hours': closed_hours,
        'hour_start': 0,
        'open_top': f'{open_top:.2f}',
        'open_time': open_time,
        'close_time': close_time,
        'barbers': barbers,
        'selected_barber': selected_barber,
        'show_barber_select': len(barbers) > 1 and not (request.user.is_barber and profile),
        'px_per_hour': px_per_hour,
        'grid_height': grid_height,
        'show_now': show_now,
        'now_top': now_top,
        'now_day_index': now.isoweekday() % 7 if show_now else None,
        'month_label': month_label,
        'status_choices': Appointment.Status.choices,
    })


@role_required(User.Role.BARBER, User.Role.OWNER)
@shop_required
def clients_view(request):
    shop = request.user.shop
    profile = getattr(request.user, 'barber_profile', None)
    qs = Appointment.objects.filter(shop=shop)
    if request.user.is_barber and profile:
        qs = qs.filter(barber=profile)

    clients_map = {}
    for appt in qs.select_related('client').order_by('-starts_at'):
        key = appt.client_id or appt.guest_phone or appt.guest_name
        if key not in clients_map:
            clients_map[key] = {
                'name': appt.client_display,
                'phone': appt.guest_phone,
                'email': appt.guest_email or (appt.client.email if appt.client else ''),
                'count': 0,
                'last': appt.starts_at,
            }
        clients_map[key]['count'] += 1
        if appt.starts_at > clients_map[key]['last']:
            clients_map[key]['last'] = appt.starts_at

    clients = sorted(clients_map.values(), key=lambda c: c['last'], reverse=True)
    return render(request, 'dashboard/clients.html', {'clients': clients})


@role_required(User.Role.BARBER, User.Role.OWNER)
@shop_required
def metrics_view(request):
    shop = request.user.shop
    profile = getattr(request.user, 'barber_profile', None)
    qs = Appointment.objects.filter(shop=shop)
    if request.user.is_barber and profile and not request.user.is_owner:
        qs = qs.filter(barber=profile)

    metrics = _metrics_for_queryset(qs)
    by_service = (
        qs.values('service__name')
        .annotate(c=Count('id'))
        .order_by('-c')[:6]
    )
    last_14 = timezone.now() - timedelta(days=14)
    daily = (
        qs.filter(starts_at__gte=last_14)
        .annotate(day=TruncDate('starts_at'))
        .values('day')
        .annotate(c=Count('id'))
        .order_by('day')
    )

    barber_breakdown = None
    if request.user.is_owner:
        barber_breakdown = (
            BarberProfile.objects.filter(shop=shop)
            .annotate(
                total=Count('appointments'),
                done=Count('appointments', filter=Q(appointments__status=Appointment.Status.COMPLETED)),
            )
            .select_related('user')
        )

    return render(request, 'dashboard/metrics.html', {
        'metrics': metrics,
        'by_service': by_service,
        'daily': list(daily),
        'barber_breakdown': barber_breakdown,
    })


# ---- Owner settings ----

@role_required(User.Role.OWNER)
@shop_required
@require_http_methods(['GET', 'POST'])
def settings_general(request):
    shop = request.user.shop
    form = ShopGeneralForm(request.POST or None, request.FILES or None, instance=shop)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Datos generales guardados.')
        return redirect('dashboard:settings_general')
    return render(request, 'dashboard/settings_general.html', {
        'form': form,
        'shop': shop,
        'settings_tab': 'general',
    })


@role_required(User.Role.OWNER)
@shop_required
@require_http_methods(['GET', 'POST'])
def settings_form(request):
    shop = request.user.shop
    cfg = shop.form_config
    form = BookingFormConfigForm(request.POST or None, initial=cfg)
    if request.method == 'POST' and form.is_valid():
        shop.booking_form_config = form.cleaned_data
        shop.save(update_fields=['booking_form_config', 'updated_at'])
        messages.success(request, 'Formulario de reserva actualizado.')
        return redirect('dashboard:settings_form')
    return render(request, 'dashboard/settings_form.html', {
        'form': form,
        'shop': shop,
        'settings_tab': 'form',
    })


@role_required(User.Role.OWNER)
@shop_required
def settings_catalog(request):
    shop = request.user.shop
    services = shop.services.all()
    return render(request, 'dashboard/settings_catalog.html', {
        'services': services,
        'shop': shop,
        'settings_tab': 'catalog',
    })


@role_required(User.Role.OWNER)
@shop_required
@require_http_methods(['GET', 'POST'])
def service_create(request):
    shop = request.user.shop
    form = ServiceForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        svc = form.save(commit=False)
        svc.shop = shop
        svc.save()
        messages.success(request, 'Servicio creado.')
        return redirect('dashboard:settings_catalog')
    return render(request, 'dashboard/service_form.html', {'form': form, 'title': 'Nuevo servicio'})


@role_required(User.Role.OWNER)
@shop_required
@require_http_methods(['GET', 'POST'])
def service_edit(request, pk):
    shop = request.user.shop
    service = get_object_or_404(Service, pk=pk, shop=shop)
    form = ServiceForm(request.POST or None, instance=service)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Servicio actualizado.')
        return redirect('dashboard:settings_catalog')
    return render(request, 'dashboard/service_form.html', {'form': form, 'title': 'Editar servicio'})


@role_required(User.Role.OWNER)
@shop_required
def settings_establishments(request):
    shop = request.user.shop
    return render(request, 'dashboard/settings_establishments.html', {
        'establishments': shop.establishments.all(),
        'shop': shop,
        'settings_tab': 'establishments',
    })


@role_required(User.Role.OWNER)
@shop_required
@require_http_methods(['GET', 'POST'])
def establishment_create(request):
    shop = request.user.shop
    form = EstablishmentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        establishment = form.save(commit=False)
        establishment.shop = shop
        establishment.save()
        messages.success(request, 'Establecimiento creado.')
        return redirect('dashboard:settings_establishments')
    return render(request, 'dashboard/establishment_form.html', {'form': form, 'title': 'Nuevo establecimiento'})


@role_required(User.Role.OWNER)
@shop_required
@require_http_methods(['GET', 'POST'])
def establishment_edit(request, pk):
    shop = request.user.shop
    establishment = get_object_or_404(Establishment, pk=pk, shop=shop)
    form = EstablishmentForm(request.POST or None, instance=establishment)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Establecimiento actualizado.')
        return redirect('dashboard:settings_establishments')
    return render(request, 'dashboard/establishment_form.html', {'form': form, 'title': 'Editar establecimiento'})


@role_required(User.Role.OWNER)
@shop_required
def settings_barbers(request):
    shop = request.user.shop
    barbers = shop.barbers.select_related('user', 'establishment').all()
    return render(request, 'dashboard/settings_barbers.html', {
        'barbers': barbers,
        'shop': shop,
        'settings_tab': 'barbers',
    })


@role_required(User.Role.OWNER)
@shop_required
@require_http_methods(['GET', 'POST'])
def barber_create(request):
    shop = request.user.shop
    user_form = OwnerCreateUserForm(request.POST or None, initial={'role': User.Role.BARBER})
    profile_form = BarberProfileForm(request.POST or None, request.FILES or None, shop=shop)
    schedule_form = BarberWorkHoursForm(request.POST or None)
    if request.method == 'POST' and user_form.is_valid() and profile_form.is_valid() and schedule_form.is_valid():
        user = user_form.save(commit=False)
        user.role = User.Role.BARBER
        user.shop = shop
        user.save()
        profile = profile_form.save(commit=False)
        profile.user = user
        profile.shop = shop
        profile.save()
        schedule_form.save(profile=profile)
        messages.success(request, 'Barbero creado.')
        return redirect('dashboard:settings_barbers')
    return render(request, 'dashboard/barber_form.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'schedule_form': schedule_form,
        'title': 'Nuevo barbero',
    })


@role_required(User.Role.OWNER)
@shop_required
@require_http_methods(['GET', 'POST'])
def barber_edit(request, pk):
    shop = request.user.shop
    profile = get_object_or_404(BarberProfile, pk=pk, shop=shop)
    profile.ensure_work_hours()
    profile_form = BarberProfileForm(
        request.POST or None,
        request.FILES or None,
        instance=profile,
        shop=shop,
    )
    schedule_form = BarberWorkHoursForm(request.POST or None, profile=profile)
    if request.method == 'POST' and profile_form.is_valid() and schedule_form.is_valid():
        profile_form.save()
        schedule_form.save(profile=profile)
        messages.success(request, 'Barbero actualizado.')
        return redirect('dashboard:settings_barbers')
    return render(request, 'dashboard/barber_edit.html', {
        'profile': profile,
        'profile_form': profile_form,
        'schedule_form': schedule_form,
        'title': 'Editar barbero',
    })


# ---- Superadmin ----

@role_required(User.Role.SUPERADMIN)
def superadmin_home(request):
    shops = Barbershop.objects.annotate(
        member_count=Count('members'),
        appt_count=Count('appointments'),
    ).order_by('-created_at')
    users = User.objects.select_related('shop').order_by('-date_joined')[:20]
    stats = {
        'shops': Barbershop.objects.count(),
        'users': User.objects.count(),
        'appointments': Appointment.objects.count(),
        'active_shops': Barbershop.objects.filter(is_active=True).count(),
    }
    return render(request, 'dashboard/superadmin.html', {
        'shops': shops,
        'users': users,
        'stats': stats,
    })


@role_required(User.Role.SUPERADMIN)
@require_http_methods(['GET', 'POST'])
def superadmin_shop_create(request):
    form = ShopGeneralForm(request.POST or None, request.FILES or None)
    owner_email = request.POST.get('owner_email', '').strip()
    owner_password = request.POST.get('owner_password', '').strip()
    if request.method == 'POST' and form.is_valid() and owner_email and owner_password:
        shop = form.save()
        owner = User.objects.create_user(
            email=owner_email,
            password=owner_password,
            role=User.Role.OWNER,
            shop=shop,
            first_name=request.POST.get('owner_first_name', ''),
            last_name=request.POST.get('owner_last_name', ''),
        )
        messages.success(request, f'Tienda {shop.name} y dueño {owner.email} creados.')
        return redirect('dashboard:superadmin')
    return render(request, 'dashboard/superadmin_shop_form.html', {'form': form})


@role_required(User.Role.SUPERADMIN)
@require_http_methods(['GET', 'POST'])
def superadmin_shop_edit(request, pk):
    shop = get_object_or_404(Barbershop, pk=pk)
    form = ShopGeneralForm(request.POST or None, request.FILES or None, instance=shop)
    if request.method == 'POST':
        if 'toggle_active' in request.POST:
            shop.is_active = not shop.is_active
            shop.save(update_fields=['is_active'])
            messages.success(request, 'Estado de tienda actualizado.')
            return redirect('dashboard:superadmin_shop_edit', pk=pk)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tienda actualizada.')
            return redirect('dashboard:superadmin')
    members = shop.members.all()
    return render(request, 'dashboard/superadmin_shop_edit.html', {
        'form': form,
        'shop': shop,
        'members': members,
    })


@role_required(User.Role.SUPERADMIN)
def superadmin_users(request):
    users = User.objects.select_related('shop').order_by('-date_joined')
    return render(request, 'dashboard/superadmin_users.html', {'users': users})


@role_required(User.Role.SUPERADMIN)
@require_http_methods(['POST'])
def superadmin_user_toggle(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user != request.user:
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
        messages.success(request, f'Usuario {user.email} actualizado.')
    return redirect('dashboard:superadmin_users')


@role_required(User.Role.BARBER, User.Role.OWNER)
@require_http_methods(['POST'])
def appointment_status(request, pk):
    shop = request.user.shop
    appt = get_object_or_404(Appointment, pk=pk, shop=shop)
    if request.user.is_barber:
        profile = getattr(request.user, 'barber_profile', None)
        if profile and appt.barber_id != profile.id:
            messages.error(request, 'No podés modificar esta reserva.')
            return redirect('dashboard:calendar')
    status = request.POST.get('status')
    if status in dict(Appointment.Status.choices):
        appt.status = status
        appt.save(update_fields=['status', 'updated_at'])
        messages.success(request, 'Estado actualizado.')
    return redirect(request.META.get('HTTP_REFERER', 'dashboard:calendar'))
