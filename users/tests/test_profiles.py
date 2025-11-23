# users/tests/test_profiles.py (VERSIÓN MÍNIMA FASE 1)

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users.models import Role, User
from users.models_profiles import (ClienteProfile, FerianteProfile,
                                   RepartidorProfile)

# ==========================================================
# FIXTURES
# ==========================================================


@pytest.fixture
def api_client():
    """Cliente API para realizar peticiones HTTP."""
    return APIClient()


@pytest.fixture
def role_feriante(db):
    """Crea o recupera el rol Feriante."""
    role, _ = Role.objects.get_or_create(
        name="Feriante", defaults={"description": "Vendedor de feria"}
    )
    return role


@pytest.fixture
def user_feriante(db, role_feriante):
    """Crea un usuario con rol Feriante."""
    return User.objects.create_user(
        email="test_feriante_fase1@feria.cl", password="Pass1234", role=role_feriante
    )


# ==========================================================
# TEST 1: Crear feriante → se crea su perfil (signal)
# ==========================================================


@pytest.mark.django_db
def test_feriante_profile_created_by_signal(user_feriante):
    """
    Verifica que al crear un User con rol Feriante,
    se crea automáticamente su FerianteProfile por la signal.
    """
    assert FerianteProfile.objects.filter(user=user_feriante).exists()

    perfil = FerianteProfile.objects.get(user=user_feriante)
    assert perfil.user == user_feriante


# ==========================================================
# TEST 2: /me/ devuelve perfil de feriante
# ==========================================================


@pytest.mark.django_db
def test_me_returns_feriante_profile(api_client, user_feriante):
    """
    Verifica que GET /api/v1/me/ devuelve 200 OK
    y contiene los datos del perfil del feriante autenticado.
    """
    # Autenticar al usuario
    api_client.force_authenticate(user=user_feriante)

    # Llamar al endpoint /me/
    url = reverse("me-list")  # ← CORREGIDO
    response = api_client.get(url)

    # Verificar respuesta
    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "success"

    # Verificar que devuelve el user_id correcto
    data = response.data["data"]
    assert str(data["id"]) == str(user_feriante.id)  # ← CORREGIDO: 'id' no 'user'


# ==========================================================
# TEST 3: Sin auth → 401
# ==========================================================


@pytest.mark.django_db
def test_me_requires_authentication(api_client):
    """
    Verifica que GET /api/v1/me/ sin autenticación
    devuelve 401 UNAUTHORIZED.
    """
    url = reverse("me-list")  # ← CORREGIDO
    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
