# market/tests/test_market.py

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from market.models import Feria, Producto, Puesto
from users.models import Role, User

# ==========================================================
# FIXTURES
# ==========================================================


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def role_feriante(db):
    role, _ = Role.objects.get_or_create(
        name="Feriante", defaults={"description": "Vendedor de feria"}
    )
    return role


@pytest.fixture
def feriante_user(db, role_feriante):
    return User.objects.create_user(
        email="feriante@test.cl", password="Pass1234", role=role_feriante
    )


@pytest.fixture
def otro_feriante(db, role_feriante):
    return User.objects.create_user(
        email="otro_feriante@test.cl", password="Pass1234", role=role_feriante
    )


@pytest.fixture
def feria(db):
    return Feria.objects.create(
        nombre="Feria Lo Valledor",
        comuna="Pedro Aguirre Cerda",
        direccion="Av. Lo Valledor 1234",
        activa=True,
    )


@pytest.fixture
def puesto(db, feria, feriante_user):
    return Puesto.objects.create(
        feria=feria,
        feriante=feriante_user,
        nombre="Puesto de Verduras",
        categoria="Verduras",
        activo=True,
    )


# ==========================================================
# TESTS FERIA
# ==========================================================


@pytest.mark.django_db
def test_listar_ferias_publico(api_client, feria):
    """
    Cualquiera puede listar ferias sin autenticación.
    """
    url = reverse("feria-list")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) >= 1
    nombres = [f["nombre"] for f in response.data]
    assert "Feria Lo Valledor" in nombres


# ==========================================================
# TESTS PUESTO
# ==========================================================


@pytest.mark.django_db
def test_feriante_crea_puesto(api_client, feriante_user, feria):
    """
    Un feriante autenticado puede crear un puesto.
    """
    api_client.force_authenticate(user=feriante_user)

    url = reverse("puesto-list")
    data = {"feria": str(feria.id), "nombre": "Puesto de Frutas", "categoria": "Frutas"}
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["nombre"] == "Puesto de Frutas"
    # DRF devuelve UUID, lo comparamos como string
    assert str(response.data["feriante"]) == str(feriante_user.id)


@pytest.mark.django_db
def test_anonimo_no_puede_crear_puesto(api_client, feria):
    """
    Un usuario no autenticado NO puede crear un puesto.
    """
    url = reverse("puesto-list")
    data = {"feria": str(feria.id), "nombre": "Puesto Anónimo", "categoria": "General"}
    response = api_client.post(url, data, format="json")

    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    )


@pytest.mark.django_db
def test_otro_feriante_no_puede_editar_puesto(api_client, puesto, otro_feriante):
    """
    Un feriante NO puede editar el puesto de otro.
    """
    api_client.force_authenticate(user=otro_feriante)

    url = reverse("puesto-detail", args=[puesto.id])
    data = {"nombre": "Puesto Hackeado"}
    response = api_client.patch(url, data, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN


# ==========================================================
# TESTS PRODUCTO
# ==========================================================


@pytest.mark.django_db
def test_feriante_crea_producto_en_su_puesto(api_client, feriante_user, puesto):
    """
    Un feriante puede crear productos en su propio puesto.
    """
    api_client.force_authenticate(user=feriante_user)

    url = reverse("producto-list")
    data = {
        "puesto": str(puesto.id),
        "nombre": "Tomate",
        "precio": "1500",
        "stock": 100,
        "unidad": "kg",
    }
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["nombre"] == "Tomate"
    assert str(response.data["puesto"]) == str(puesto.id)


@pytest.mark.django_db
def test_otro_feriante_no_crea_producto_exitosamente_en_puesto_ajeno(
    api_client, puesto, otro_feriante
):
    """
    Otro feriante no debería crear producto exitosamente en un puesto ajeno.
    En la implementación actual esto responde 400 (validación) o 403 (permisos),
    pero NUNCA debe ser 201.
    """
    api_client.force_authenticate(user=otro_feriante)

    url = reverse("producto-list")
    data = {
        "puesto": str(puesto.id),
        "nombre": "Producto Falso",
        "precio": "1000",
        "stock": 10,
    }
    response = api_client.post(url, data, format="json")

    # Lo importante: no debe ser creado con éxito
    assert response.status_code != status.HTTP_201_CREATED
    assert response.status_code in (
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_403_FORBIDDEN,
    )


@pytest.mark.django_db
def test_listar_productos_publico(api_client, puesto, feriante_user):
    """
    Cualquiera puede listar productos sin autenticación.
    """
    # Crear un producto primero
    Producto.objects.create(
        puesto=puesto, nombre="Lechuga", precio=800, stock=50, activo=True
    )

    url = reverse("producto-list")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) >= 1
    nombres = [p["nombre"] for p in response.data]
    assert "Lechuga" in nombres
