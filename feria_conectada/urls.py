# feria_conectada/urls.py (Archivo principal)

from django.contrib import admin
from django.urls import path, include

# 1. Importar las vistas de Spectacular
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),

    # API v1
    path("api/v1/core/", include("core.urls")),
    path("api/v1/auth/", include("djoser.urls")),
    path("api/v1/auth/", include("djoser.urls.jwt")),
    
    # Conecta las rutas de users/roles definidas en users/urls.py
    path("api/v1/", include("users.urls")), 
]

# 2. Agregar las rutas de documentación
urlpatterns += [
    # Genera el esquema OpenAPI (JSON/YAML)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    
    # Proporciona la interfaz de usuario de Swagger (redirecciona a schema)
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]