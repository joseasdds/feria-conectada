
from rest_framework.routers import DefaultRouter
from market.views import FeriaViewSet, PuestoViewSet, ProductoViewSet

router = DefaultRouter()
router.register(r"ferias", FeriaViewSet, basename="feria")
router.register(r"puestos", PuestoViewSet, basename="puesto")
router.register(r"productos", ProductoViewSet, basename="producto")

urlpatterns = router.urls