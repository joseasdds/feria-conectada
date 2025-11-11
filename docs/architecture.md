# Arquitectura — Feria Conectada

## Objetivo
Backend escalable, seguro y modular que soporte:
- Alta concurrencia de lectura (catálogo/marketplace)
- Flujos transaccionales (pedidos/pagos/entregas)
- Evolución por dominios (DDD light)

## Visión general
- API REST sin estado (stateless)
- JWT para autenticación
- PostgreSQL como fuente de verdad
- Despliegue cloud-ready (Docker/AWS)

## Estructura de directorios (resumen)
feria_conectada/
├─ feria_conectada/ # proyecto
│ ├─ settings.py # settings consolidado
│ ├─ urls.py # enruta API y docs
│ └─ wsgi.py
├─ core/ # utilidades compartidas
├─ users/ # User/Role + auth
│ ├─ models.py
│ ├─ managers.py
│ ├─ serializers.py
│ ├─ views.py
│ ├─ urls.py
│ └─ admin.py
├─ market/ # ferias, puestos, productos (fase próxima)
├─ orders/ # pedidos, items, pagos (fase próxima)
├─ delivery/ # asignaciones y logística (fase próxima)
└─ docs/ # documentación del proyecto


## Dominios y modelos (MVP)
- Users
  - Role(id: UUID, name: {ADMIN, FERIANTE, CLIENTE, REPARTIDOR}, description)
  - User(id: UUID, email, full_name, phone, role[Fk], is_active, is_staff, is_verified, timestamps)
  - Perfiles por rol (fase próxima): FerianteProfile, ClienteProfile, RepartidorProfile (OneToOne con User)

- Market (fase próxima)
  - Feria, Puesto, Producto, Categoría

- Orders (fase próxima)
  - Order, OrderItem, Payment, PaymentLog

- Delivery (fase próxima)
  - DeliveryAssignment (repartidor ←→ order), estados

## Autenticación y permisos
- Login via JWT: `/api/v1/auth/jwt/create/`
- Djoser:
  - registro de usuarios: `/api/v1/auth/users/`
  - perfil del usuario autenticado: `/api/v1/auth/users/me/`
- Permisos por defecto:
  - DEBUG=True: AllowAny
  - Producción: IsAuthenticated por defecto; reglas específicas por vista
- Roles dirigen capacidades; reglas finas se aplican en `permissions.py` por app

## Configuración clave
- PK UUID para escalabilidad y seguridad (no predecibles)
- CORS habilitado para frontend local: `http://localhost:3000` y `http://localhost:19006`
- drf-spectacular para OpenAPI/Swagger (`/api/docs/`)

## Flujo típico
1. Usuario se registra o un admin lo crea y asigna `role`
2. Usuario obtiene JWT (access/refresh)
3. Cliente navega catálogo (market), crea pedido (orders)
4. Feriante confirma y prepara pedido
5. Repartidor toma asignación (delivery)
6. Pago confirmado por webhook (payments)
7. Notificaciones por email/real-time (futuro)

## Entornos
- Local: DEBUG=True, DB local, CORS abiertos
- Staging: DEBUG=False, RDS/S3, logs, métricas
- Prod: DEBUG=False, WAF/HTTPS, rotación de secretos

## Observabilidad (a implementar)
- Logging estructurado a consola (root INFO)
- Trazas y métricas: CloudWatch / Grafana (futuro)

## Roadmap de módulos próximos
1. Perfiles por rol (Users)
2. Market (Feria/Puesto/Producto)
3. Orders + Payments
4. Delivery + tracking
5. Notificaciones (emails / websockets)