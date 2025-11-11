# feria_conectada/urls.py

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # Panel de administración de Django
    path("admin/", admin.site.urls),

    # -------------------------------
    # API v1 - Endpoints principales
    # -------------------------------
    path("api/v1/core/", include("core.urls")),
    path("api/v1/auth/", include("djoser.urls")),
    path("api/v1/auth/", include("djoser.urls.jwt")),
    path("api/v1/", include("users.urls")),  # Rutas del módulo users (usuarios y roles)
]

# -------------------------------
# Documentación de la API (Swagger + OpenAPI)
# -------------------------------
urlpatterns += [
    # Genera el esquema OpenAPI (JSON/YAML)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),

    # Interfaz Swagger UI para visualizar la documentación
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
