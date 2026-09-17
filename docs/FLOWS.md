# Barber24 — Flujos

## Reserva pública
1. Cliente abre `/b/{slug}/`
2. Completa formulario (campos según config del dueño)
3. POST crea `Appointment` pendiente
4. Redirect a `wa.me/{sucursal}?text=mensaje`

## Barbero
Login → Inicio (métricas propias) → Agenda / Clientes / Métricas / Perfil

## Dueño
Login → Resumen tienda → Agenda / Clientes / Métricas globales → Config:
General · Catálogo · Sucursales · Barberos · Formulario

## Cliente
Google login → Mis reservas / Perfil

## Superadmin
Login → Panel tiendas → Crear/editar tiendas · Activar/desactivar usuarios
