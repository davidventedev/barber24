# Barber24 — Backend Schema

## User
- email (unique), first_name, last_name, role [client|barber|owner|superadmin]
- phone, avatar, google_id
- shop (FK nullable — staff pertenece a una tienda)

## Barbershop
- name, slug (unique), logo, primary_color
- is_active, created_at
- booking_form_config (JSON: fields visibility/labels)

## Branch (Sucursal)
- shop FK, name, address, city
- whatsapp_number, is_active

## Service (Catálogo)
- shop FK, name, description, duration_min, price
- is_active, order

## BarberProfile
- user FK, shop FK, bio, specialties
- branch FK nullable, is_active, color_calendar

## ClientProfile
- user FK, notes

## Appointment
- shop, branch, barber, client (nullable), service
- guest_name, guest_phone, guest_email
- starts_at, ends_at, status [pending|confirmed|completed|cancelled|no_show]
- notes, source [web|manual]

## Indexes
- Appointment(shop, starts_at), Appointment(barber, starts_at)
- Barbershop(slug)
