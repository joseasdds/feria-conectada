from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"users", views.UserViewSet, basename="users")
router.register(r"roles", views.RoleViewSet, basename="roles")

urlpatterns = router.urls