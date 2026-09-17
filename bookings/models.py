from django.conf import settings
from django.db import models
from django.utils import timezone


class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        CONFIRMED = 'confirmed', 'Confirmada'
        COMPLETED = 'completed', 'Completada'
        CANCELLED = 'cancelled', 'Cancelada'
        NO_SHOW = 'no_show', 'No asistió'

    class Source(models.TextChoices):
        WEB = 'web', 'Web'
        MANUAL = 'manual', 'Manual'

    shop = models.ForeignKey('shops.Barbershop', on_delete=models.CASCADE, related_name='appointments')
    branch = models.ForeignKey('shops.Branch', on_delete=models.PROTECT, related_name='appointments')
    barber = models.ForeignKey(
        'shops.BarberProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments',
    )
    service = models.ForeignKey('shops.Service', on_delete=models.PROTECT, related_name='appointments')
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments',
    )
    guest_name = models.CharField(max_length=150)
    guest_phone = models.CharField(max_length=30)
    guest_email = models.EmailField(blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.WEB)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'reserva'
        verbose_name_plural = 'reservas'
        ordering = ['-starts_at']
        indexes = [
            models.Index(fields=['shop', 'starts_at']),
            models.Index(fields=['barber', 'starts_at']),
            models.Index(fields=['client', 'starts_at']),
        ]

    def __str__(self):
        return f'{self.guest_name} — {self.starts_at:%d/%m %H:%M}'

    @property
    def client_display(self):
        if self.client:
            return self.client.full_name
        return self.guest_name

    @property
    def is_upcoming(self):
        return self.starts_at >= timezone.now() and self.status in (
            self.Status.PENDING,
            self.Status.CONFIRMED,
        )

    def build_whatsapp_message(self):
        barber_name = self.barber.user.full_name if self.barber else 'Sin preferencia'
        lines = [
            f'¡Hola! Quiero reservar en *{self.shop.name}*',
            f'',
            f'👤 *Cliente:* {self.guest_name}',
            f'📱 *Teléfono:* {self.guest_phone}',
            f'✂️ *Servicio:* {self.service.name}',
            f'📍 *Sucursal:* {self.branch.name}',
            f'🧑‍🎤 *Barbero:* {barber_name}',
            f'🗓 *Fecha:* {self.starts_at:%d/%m/%Y}',
            f'⏰ *Hora:* {self.starts_at:%H:%M}',
            f'⏱ *Duración:* {self.service.duration_min} min',
        ]
        if self.notes:
            lines.append(f'📝 *Notas:* {self.notes}')
        return '\n'.join(lines)

    def whatsapp_url(self):
        from urllib.parse import quote
        phone = ''.join(c for c in self.branch.whatsapp_number if c.isdigit())
        text = quote(self.build_whatsapp_message())
        return f'https://wa.me/{phone}?text={text}'
