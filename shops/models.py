from django.db import models
from django.utils.text import slugify


DEFAULT_FORM_CONFIG = {
    'show_barber': True,
    'show_notes': True,
    'show_email': False,
    'require_phone': True,
    'title': 'Reservá tu turno',
    'subtitle': 'Elegí servicio, sucursal y horario',
    'cta_label': 'Confirmar por WhatsApp',
    'success_message': '¡Listo! Te redirigimos a WhatsApp para confirmar.',
}


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


class Branch(models.Model):
    shop = models.ForeignKey(Barbershop, on_delete=models.CASCADE, related_name='branches')
    name = models.CharField(max_length=120)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    whatsapp_number = models.CharField(
        'WhatsApp',
        max_length=20,
        help_text='Solo dígitos con código de país, ej: 5491112345678',
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'sucursal'
        verbose_name_plural = 'sucursales'
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
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='barbers',
    )
    bio = models.TextField(blank=True)
    specialties = models.CharField(max_length=255, blank=True)
    calendar_color = models.CharField(max_length=7, default='#EAC452')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'perfil de barbero'
        verbose_name_plural = 'perfiles de barberos'

    def __str__(self):
        return self.user.full_name
