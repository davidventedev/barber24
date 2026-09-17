from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from bookings.models import Appointment
from shops.models import BarberProfile, Barbershop, Branch, Service

User = get_user_model()


class Command(BaseCommand):
    help = 'Carga datos demo: tienda, dueño, barbero, servicios y reservas'

    def handle(self, *args, **options):
        admin, _ = User.objects.get_or_create(
            email='admin@barber24.com',
            defaults={
                'role': User.Role.SUPERADMIN,
                'is_staff': True,
                'is_superuser': True,
                'first_name': 'Super',
                'last_name': 'Admin',
            },
        )
        admin.role = User.Role.SUPERADMIN
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password('admin123')
        admin.save()

        shop, created = Barbershop.objects.get_or_create(
            slug='demo-cuts',
            defaults={
                'name': 'Demo Cuts',
                'tagline': 'Estilo clásico, vibe moderno',
                'city': 'Buenos Aires',
                'phone': '1112345678',
                'email': 'hola@democuts.com',
            },
        )

        owner, _ = User.objects.get_or_create(
            email='dueno@democuts.com',
            defaults={
                'role': User.Role.OWNER,
                'shop': shop,
                'first_name': 'Martín',
                'last_name': 'Dueño',
            },
        )
        owner.role = User.Role.OWNER
        owner.shop = shop
        owner.set_password('dueno123')
        owner.save()

        barber_user, _ = User.objects.get_or_create(
            email='barbero@democuts.com',
            defaults={
                'role': User.Role.BARBER,
                'shop': shop,
                'first_name': 'Lucas',
                'last_name': 'Ramos',
                'phone': '1198765432',
            },
        )
        barber_user.role = User.Role.BARBER
        barber_user.shop = shop
        barber_user.set_password('barbero123')
        barber_user.save()

        branch, _ = Branch.objects.get_or_create(
            shop=shop,
            name='Palermo',
            defaults={
                'address': 'Av. Santa Fe 3200',
                'city': 'CABA',
                'whatsapp_number': '5491112345678',
            },
        )
        Branch.objects.get_or_create(
            shop=shop,
            name='Belgrano',
            defaults={
                'address': 'Cabildo 2100',
                'city': 'CABA',
                'whatsapp_number': '5491198765432',
            },
        )

        profile, _ = BarberProfile.objects.get_or_create(
            user=barber_user,
            defaults={
                'shop': shop,
                'branch': branch,
                'bio': 'Especialista en fades y barbas.',
                'specialties': 'Fade, Barba, Diseño',
            },
        )

        services_data = [
            ('Corte clásico', 30, '8500'),
            ('Corte + barba', 45, '12000'),
            ('Barba', 20, '5500'),
            ('Diseño', 40, '10000'),
        ]
        services = []
        for i, (name, duration, price) in enumerate(services_data):
            svc, _ = Service.objects.get_or_create(
                shop=shop,
                name=name,
                defaults={'duration_min': duration, 'price': Decimal(price), 'order': i},
            )
            services.append(svc)

        if not Appointment.objects.filter(shop=shop).exists():
            now = timezone.now()
            Appointment.objects.create(
                shop=shop,
                branch=branch,
                barber=profile,
                service=services[0],
                guest_name='Juan Pérez',
                guest_phone='1155551111',
                starts_at=now + timedelta(hours=3),
                ends_at=now + timedelta(hours=3, minutes=30),
                status=Appointment.Status.CONFIRMED,
            )
            Appointment.objects.create(
                shop=shop,
                branch=branch,
                barber=profile,
                service=services[1],
                guest_name='Carlos Gómez',
                guest_phone='1155552222',
                starts_at=now + timedelta(days=1, hours=2),
                ends_at=now + timedelta(days=1, hours=2, minutes=45),
                status=Appointment.Status.PENDING,
            )
            Appointment.objects.create(
                shop=shop,
                branch=branch,
                barber=profile,
                service=services[0],
                guest_name='Diego Ruiz',
                guest_phone='1155553333',
                starts_at=now - timedelta(days=2),
                ends_at=now - timedelta(days=2) + timedelta(minutes=30),
                status=Appointment.Status.COMPLETED,
            )

        self.stdout.write(self.style.SUCCESS('Demo lista.'))
        self.stdout.write('  Superadmin: admin@barber24.com / admin123')
        self.stdout.write('  Dueño:      dueno@democuts.com / dueno123')
        self.stdout.write('  Barbero:    barbero@democuts.com / barbero123')
        self.stdout.write(f'  Reservas:   /b/{shop.slug}/')
