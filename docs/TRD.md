# Barber24 — Technical Requirements Document (TRD)

## Stack
- **Backend:** Django 4.2 + Django Templates
- **Auth:** django-allauth (Google OAuth) + auth nativa
- **DB:** SQLite (dev) / PostgreSQL-ready
- **Static:** WhiteNoise
- **PWA:** Service Worker + Web Manifest
- **Frontend:** HTML/CSS/JS mobile-first (sin framework pesado)

## Multitenancy
Soft multi-tenant: modelo `Barbershop` (tenant). Toda entidad operativa lleva `shop` FK. Aislamiento por middleware/`shop_id` en queries.

## Apps Django
| App | Responsabilidad |
|-----|-----------------|
| `accounts` | User custom, roles, perfiles |
| `shops` | Tenant, sucursales, catálogo, config formulario |
| `bookings` | Reservas, calendario, WhatsApp deep-link |
| `dashboard` | Vistas por rol |
| `core` | Landing, PWA assets, utilidades |

## Auth
- Email/password para staff (dueño, barbero, superadmin)
- Google OAuth para clientes (también disponible para staff)
- Middleware de rol + decoradores

## WhatsApp
Al confirmar reserva se genera URL `https://wa.me/{phone}?text={mensaje}` y se redirige al cliente.
