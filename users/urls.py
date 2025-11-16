# users/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from users.views import RoleViewSet, UserViewSet, MeViewSet
from users.users_views_auth import RegisterView, LoginView, LogoutView

router = DefaultRouter()
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'users', UserViewSet, basename='user')
router.register(r'me', MeViewSet, basename='me')  # ← genera 'me-list'

urlpatterns = [
    # ViewSets registrados en el router
    path('', include(router.urls)),

    # Autenticación JWT
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
]