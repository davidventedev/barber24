from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from accounts.decorators import role_required, shop_required
from accounts.forms import OwnerCreateUserForm, ProfileForm
from bookings.models import Appointment
from shops.forms import (
    BarberProfileForm,
    BookingFormConfigForm,
    BranchForm,
    ServiceForm,
    ShopGeneralForm,
)
from shops.models import BarberProfile, Barbershop, Branch, Service

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
    qs = Appointment.objects.filter(shop=shop).select_related('service', 'branch', 'client')
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
    recent = qs.select_related('service', 'branch', 'barber__user').order_by('-created_at')[:8]
    return render(request, 'dashboard/owner_home.html', {
        'shop': shop,
        'metrics': metrics,
        'barber_stats': barber_stats,
        'recent': recent,
    })


@role_required(User.Role.BARBER, User.Role.OWNER)
@shop_required
def calendar_view(request):
    shop = request.user.shop
    profile = getattr(request.user, 'barber_profile', None)
    week_offset = int(request.GET.get('w', 0) or 0)
    today = timezone.localdate()
    start = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    end = start + timedelta(days=7)
    qs = Appointment.objects.filter(
        shop=shop,
        starts_at__date__gte=start,
        starts_at__date__lt=end,
    ).exclude(status=Appointment.Status.CANCELLED).select_related(
        'service', 'barber__user', 'branch'
    )
    if request.user.is_barber and profile:
        qs = qs.filter(barber=profile)

    days = []
    for i in range(7):
        day = start + timedelta(days=i)
        days.append({
            'date': day,
            'items': [a for a in qs if timezone.localtime(a.starts_at).date() == day],
        })
    return render(request, 'dashboard/calendar.html', {
        'days': days,
        'start': start,
        'end': end - timedelta(days=1),
        'week_offset': week_offset,
        'prev_w': week_offset - 1,
        'next_w': week_offset + 1,
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
def settings_branches(request):
    shop = request.user.shop
    return render(request, 'dashboard/settings_branches.html', {
        'branches': shop.branches.all(),
        'shop': shop,
        'settings_tab': 'branches',
    })


@role_required(User.Role.OWNER)
@shop_required
@require_http_methods(['GET', 'POST'])
def branch_create(request):
    shop = request.user.shop
    form = BranchForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        branch = form.save(commit=False)
        branch.shop = shop
        branch.save()
        messages.success(request, 'Sucursal creada.')
        return redirect('dashboard:settings_branches')
    return render(request, 'dashboard/branch_form.html', {'form': form, 'title': 'Nueva sucursal'})


@role_required(User.Role.OWNER)
@shop_required
@require_http_methods(['GET', 'POST'])
def branch_edit(request, pk):
    shop = request.user.shop
    branch = get_object_or_404(Branch, pk=pk, shop=shop)
    form = BranchForm(request.POST or None, instance=branch)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Sucursal actualizada.')
        return redirect('dashboard:settings_branches')
    return render(request, 'dashboard/branch_form.html', {'form': form, 'title': 'Editar sucursal'})


@role_required(User.Role.OWNER)
@shop_required
def settings_barbers(request):
    shop = request.user.shop
    barbers = shop.barbers.select_related('user', 'branch').all()
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
    profile_form = BarberProfileForm(request.POST or None, shop=shop)
    if request.method == 'POST' and user_form.is_valid() and profile_form.is_valid():
        user = user_form.save(commit=False)
        user.role = User.Role.BARBER
        user.shop = shop
        user.save()
        profile = profile_form.save(commit=False)
        profile.user = user
        profile.shop = shop
        profile.save()
        messages.success(request, 'Barbero creado.')
        return redirect('dashboard:settings_barbers')
    return render(request, 'dashboard/barber_form.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'title': 'Nuevo barbero',
    })


@role_required(User.Role.OWNER)
@shop_required
@require_http_methods(['GET', 'POST'])
def barber_edit(request, pk):
    shop = request.user.shop
    profile = get_object_or_404(BarberProfile, pk=pk, shop=shop)
    profile_form = BarberProfileForm(request.POST or None, instance=profile, shop=shop)
    if request.method == 'POST' and profile_form.is_valid():
        profile_form.save()
        messages.success(request, 'Barbero actualizado.')
        return redirect('dashboard:settings_barbers')
    return render(request, 'dashboard/barber_edit.html', {
        'profile': profile,
        'profile_form': profile_form,
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
