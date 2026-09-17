# Barber24

SaaS multitenant para gestión de reservas de barberías. Progressive Web App con Django.

## Stack
- Django 4.2 + Templates
- django-allauth (Google OAuth)
- WhiteNoise + Service Worker (PWA)
- SQLite (dev)

## Setup rápido

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Abrí http://127.0.0.1:8000/

### Cuentas demo
| Rol | Email | Password |
|-----|-------|----------|
| Superadmin | admin@barber24.com | admin123 |
| Dueño | dueno@democuts.com | dueno123 |
| Barbero | barbero@democuts.com | barbero123 |

Link de reservas demo: http://127.0.0.1:8000/b/demo-cuts/

### Google OAuth
1. Creá credenciales OAuth en Google Cloud Console
2. Redirect URI: `http://127.0.0.1:8000/accounts/google/login/callback/`
3. Completá `GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET` en `.env`

## Roles
- **Cliente** — historial de reservas (login Google)
- **Barbero** — calendario, clientes, métricas, perfil
- **Dueño** — métricas globales + config (General, Catálogo, Sucursales, Barberos, Formulario)
- **Superadmin** — todas las tiendas y usuarios

## Paleta
- Fondo: `#000000`
- Primario: `#EAC452`
- Superficies: `#141414` / `#1c1c1c`
