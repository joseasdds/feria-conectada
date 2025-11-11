# Feria Conectada — Backend (Django + DRF)

Plataforma para digitalizar ferias libres en Chile conectando feriantes, clientes y repartidores.  
Backend modular con Django REST Framework, JWT y PostgreSQL, pensado para despliegues cloud.

## Stack principal
- Django 5 + Django REST Framework
- Autenticación: SimpleJWT + Djoser (login por email)
- Base de datos: PostgreSQL (UUID como PK)
- CORS: django-cors-headers
- Esquema OpenAPI: drf-spectacular
- Infra listos para Docker/AWS (a implementar en fases)

## Módulos (apps)
- core: utilidades comunes, configuraciones y helpers
- users: User/Role, autenticación y administración
- market: ferias, puestos, productos (fase próxima)
- orders: pedidos, items, pagos (fase próxima)
- delivery: asignaciones y trazabilidad de entregas (fase próxima)

## Endpoints base
- Auth JWT
  - POST /api/v1/auth/jwt/create/
  - POST /api/v1/auth/jwt/refresh/
  - POST /api/v1/auth/jwt/verify/
- Djoser (registro y gestión de usuarios)
  - POST /api/v1/auth/users/
  - GET  /api/v1/auth/users/me/
- Roles
  - GET  /api/v1/roles/
- Documentación OpenAPI
  - GET  /api/docs/  (Swagger UI)
  - GET  /api/schema/ (OpenAPI JSON)

## Estado del proyecto
- Fase 0 (arquitectura base): completa
- Fase 1 (perfiles por rol): siguiente
- Fases Market/Orders/Delivery/Payments: planificadas

## Licencia
Privado. Uso interno del equipo de Feria Conectada.