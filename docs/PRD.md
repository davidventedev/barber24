# Barber24 — Product Requirements Document (PRD)

## Visión
Barber24 es un SaaS multitenant que permite a barberías gestionar reservas, catálogo, sucursales y barberos, con un formulario público de reservas que notifica por WhatsApp.

## Roles
| Rol | Descripción |
|-----|-------------|
| **Cliente** | Login con Google, historial de reservas |
| **Barbero** | Calendario, clientes, métricas propias, perfil |
| **Dueño** | Todo lo del barbero + métricas globales + configuración de tienda |
| **Superadmin** | Administración de todas las tiendas y usuarios |

## Funcionalidades

### Público
- Landing SaaS
- Link de reservas por barbería (`/b/{slug}/`)
- Formulario personalizable que abre WhatsApp con el mensaje a la sucursal

### Barbero
- Calendario de citas
- Listado de clientes
- Métricas de trabajos
- Perfil

### Dueño
- Métricas de todos los barberos
- Configuración: General, Catálogo, Sucursales, Barberos
- Personalización del formulario de reserva

### Cliente
- Login Google
- Historial de reservas

### Superadmin
- CRUD tiendas y usuarios
