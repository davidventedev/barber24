from datetime import time

from django.db import models
from django.utils.text import slugify


DEFAULT_FORM_CONFIG = {
    'show_barber': True,
    'show_notes': True,
    'show_email': False,
    'require_phone': True,
    'title': 'Reservá tu turno',
    'subtitle': 'Elegí servicio, establecimiento y horario',
    'cta_label': 'Confirmar por WhatsApp',
    'success_message': '¡Listo! Te redirigimos a WhatsApp para confirmar.',
}

DEFAULT_OPEN_TIME = time(9, 0)
DEFAULT_CLOSE_TIME = time(20, 0)


class Barbershop(models.Model):
    name = models.CharField('nombre', max_length=150)
    slug = models.SlugField(unique=True, max_length=160)
    tagline = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='shops/', blank=True, null=True)
    cover = models.ImageField(upload_to='shops/covers/', blank=True, null=True)
    primary_color = models.CharField(max_length=7, default='#EAC452')
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    booking_form_config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'barbería'
        verbose_name_plural = 'barberías'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or 'barberia'
            slug = base
            i = 1
            while Barbershop.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{i}'
                i += 1
            self.slug = slug
        if not self.booking_form_config:
            self.booking_form_config = DEFAULT_FORM_CONFIG.copy()
        super().save(*args, **kwargs)

    @property
    def form_config(self):
        cfg = DEFAULT_FORM_CONFIG.copy()
        cfg.update(self.booking_form_config or {})
        return cfg

    @property
    def booking_url_path(self):
        return f'/b/{self.slug}/'


class Establishment(models.Model):
    shop = models.ForeignKey(Barbershop, on_delete=models.CASCADE, related_name='establishments')
    name = models.CharField(max_length=120)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    whatsapp_number = models.CharField(
        'WhatsApp',
        max_length=20,
        help_text='Solo dígitos con código de país, ej: 5491112345678',
    )
    open_time = models.TimeField('abre a', default=DEFAULT_OPEN_TIME)
    close_time = models.TimeField('cierra a', default=DEFAULT_CLOSE_TIME)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'establecimiento'
        verbose_name_plural = 'establecimientos'
        ordering = ['order', 'name']

    def __str__(self):
        return f'{self.name} ({self.shop.name})'


class Service(models.Model):
    shop = models.ForeignKey(Barbershop, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    duration_min = models.PositiveIntegerField('duración (min)', default=30)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'servicio'
        verbose_name_plural = 'servicios'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class BarberProfile(models.Model):
    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='barber_profile',
    )
    shop = models.ForeignKey(Barbershop, on_delete=models.CASCADE, related_name='barbers')
    establishment = models.ForeignKey(
        Establishment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='barbers',
        verbose_name='establecimiento',
    )
    bio = models.TextField(blank=True)
    specialties = models.CharField(max_length=255, blank=True)
    photo = models.ImageField(
        'foto de perfil',
        upload_to='barbers/',
        blank=True,
        null=True,
    )
    calendar_color = models.CharField(max_length=7, default='#EAC452')
    work_hours = models.JSONField(
        'horarios de trabajo',
        default=dict,
        blank=True,
        help_text='Horario por día (0=domingo … 6=sábado). Soporta varios rangos.',
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'perfil de barbero'
        verbose_name_plural = 'perfiles de barberos'

    def __str__(self):
        return self.user.full_name

    @staticmethod
    def normalize_day_hours(day_data, default_open='09:00', default_close='20:00'):
        """
        Normalize a day entry to {'off': bool, 'ranges': [{'open','close'}, ...]}.
        Accepts legacy {'open','close','off'} and the multi-range shape.
        """
        if not isinstance(day_data, dict):
            return {
                'off': False,
                'ranges': [{'open': default_open, 'close': default_close}],
            }

        ranges = []
        raw_ranges = day_data.get('ranges')
        if isinstance(raw_ranges, list) and raw_ranges:
            for item in raw_ranges:
                if not isinstance(item, dict):
                    continue
                open_s = item.get('open') or default_open
                close_s = item.get('close') or default_close
                ranges.append({'open': open_s, 'close': close_s})
        else:
            ranges.append({
                'open': day_data.get('open') or default_open,
                'close': day_data.get('close') or default_close,
            })

        if not ranges:
            ranges = [{'open': default_open, 'close': default_close}]

        return {'off': bool(day_data.get('off')), 'ranges': ranges}

    def ensure_work_hours(self):
        """Fill missing days and migrate legacy single-range entries."""
        hours = dict(self.work_hours or {})
        est = self.establishment
        open_s = (est.open_time if est else DEFAULT_OPEN_TIME).strftime('%H:%M')
        close_s = (est.close_time if est else DEFAULT_CLOSE_TIME).strftime('%H:%M')
        changed = False
        for day in range(7):
            key = str(day)
            normalized = self.normalize_day_hours(
                hours.get(key),
                default_open=open_s,
                default_close=close_s,
            )
            if hours.get(key) != normalized:
                hours[key] = normalized
                changed = True
        if changed:
            self.work_hours = hours
        return hours

    def schedule_summary(self):
        """Short human-readable weekly schedule for lists."""
        labels = ('Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb')
        hours = self.ensure_work_hours()
        parts = []
        for day, label in enumerate(labels):
            data = self.normalize_day_hours(hours.get(str(day)))
            if data.get('off'):
                continue
            ranges_txt = ', '.join(
                f"{r.get('open', '09:00')}-{r.get('close', '20:00')}"
                for r in data.get('ranges') or []
            )
            parts.append(f'{label} {ranges_txt}')
        return ' · '.join(parts) if parts else 'Sin días laborales'

    def hours_for_weekday(self, weekday):
        """
        Return list of (open_time, close_time) for Sunday-first weekday index.
        Empty list if the day is off. Intersects each range with establishment hours.
        """
        hours = self.ensure_work_hours()
        day = self.normalize_day_hours(hours.get(str(weekday)))
        if day.get('off'):
            return []

        def _parse(value, fallback):
            if not value:
                return fallback
            try:
                h, m = value.split(':')[:2]
                return time(int(h), int(m))
            except (TypeError, ValueError):
                return fallback

        est = self.establishment
        fallback_open = est.open_time if est else DEFAULT_OPEN_TIME
        fallback_close = est.close_time if est else DEFAULT_CLOSE_TIME
        intervals = []
        for rng in day.get('ranges') or []:
            open_t = _parse(rng.get('open'), fallback_open)
            close_t = _parse(rng.get('close'), fallback_close)
            if est:
                open_t = max(open_t, est.open_time)
                close_t = min(close_t, est.close_time)
            if close_t > open_t:
                intervals.append((open_t, close_t))
        intervals.sort(key=lambda pair: pair[0])
        return intervals
