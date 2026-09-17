from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.SUPERADMIN)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        CLIENT = 'client', 'Cliente'
        BARBER = 'barber', 'Barbero'
        OWNER = 'owner', 'Dueño'
        SUPERADMIN = 'superadmin', 'Superadmin'

    email = models.EmailField('email', unique=True)
    first_name = models.CharField('nombre', max_length=120, blank=True)
    last_name = models.CharField('apellido', max_length=120, blank=True)
    phone = models.CharField('teléfono', max_length=30, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CLIENT)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    shop = models.ForeignKey(
        'shops.Barbershop',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'usuario'
        verbose_name_plural = 'usuarios'
        ordering = ['email']

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        name = f'{self.first_name} {self.last_name}'.strip()
        return name or self.email.split('@')[0]

    @property
    def is_owner(self):
        return self.role == self.Role.OWNER

    @property
    def is_barber(self):
        return self.role == self.Role.BARBER

    @property
    def is_client(self):
        return self.role == self.Role.CLIENT

    @property
    def is_superadmin_role(self):
        return self.role == self.Role.SUPERADMIN or self.is_superuser

    @property
    def is_staff_role(self):
        return self.role in (self.Role.BARBER, self.Role.OWNER, self.Role.SUPERADMIN)
