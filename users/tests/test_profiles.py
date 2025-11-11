# users/tests/test_profiles.py
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models import User, Role
from users.models_profiles import FerianteProfile, ClienteProfile, RepartidorProfile


@pytest.fixture
def api_client():
    """Cliente API para realizar peticiones HTTP."""
    return APIClient()


@pytest.fixture
def roles(db):
    """Crea los roles necesarios para las pruebas."""
    return {
        'feriante': Role.objects.create(name='Feriante', description='Vendedor de feria'),
        'cliente': Role.objects.create(name='Cliente', description='Comprador'),
        'repartidor': Role.objects.create(name='Repartidor', description='Logística'),
        'admin': Role.objects.create(name='Administrador', description='Admin del sistema'),
    }


@pytest.fixture
def user_feriante(db, roles):
    """Crea un usuario con rol Feriante."""
    return User.objects.create_user(
        email='feriante@test.cl',
        password='test1234',
        role=roles['feriante']
    )


@pytest.fixture
def user_cliente(db, roles):
    """Crea un usuario con rol Cliente."""
    return User.objects.create_user(
        email='cliente@test.cl',
        password='test1234',
        role=roles['cliente']
    )


@pytest.fixture
def user_repartidor(db, roles):
    """Crea un usuario con rol Repartidor."""
    return User.objects.create_user(
        email='repartidor@test.cl',
        password='test1234',
        role=roles['repartidor']
    )


# ========================================
# 🧪 TESTS DE CREACIÓN AUTOMÁTICA (SIGNALS)
# ========================================

@pytest.mark.django_db
def test_auto_create_feriante_profile(user_feriante):
    """Verifica que se cree automáticamente un FerianteProfile al crear un usuario Feriante."""
    assert FerianteProfile.objects.filter(user=user_feriante).exists()
    perfil = FerianteProfile.objects.get(user=user_feriante)
    assert perfil.user == user_feriante
    assert perfil.rut == ''  # Valor por defecto


@pytest.mark.django_db
def test_auto_create_cliente_profile(user_cliente):
    """Verifica que se cree automáticamente un ClienteProfile al crear un usuario Cliente."""
    assert ClienteProfile.objects.filter(user=user_cliente).exists()
    perfil = ClienteProfile.objects.get(user=user_cliente)
    assert perfil.user == user_cliente
    assert perfil.direccion_entrega == ''


@pytest.mark.django_db
def test_auto_create_repartidor_profile(user_repartidor):
    """Verifica que se cree automáticamente un RepartidorProfile al crear un usuario Repartidor."""
    assert RepartidorProfile.objects.filter(user=user_repartidor).exists()
    perfil = RepartidorProfile.objects.get(user=user_repartidor)
    assert perfil.user == user_repartidor
    assert perfil.vehiculo == ''


# ========================================
# 🧪 TESTS DE ENDPOINT /me/ (GET)
# ========================================

@pytest.mark.django_db
def test_get_me_profile_feriante(api_client, user_feriante):
    """Test GET /api/v1/me/ para usuario Feriante autenticado."""
    api_client.force_authenticate(user=user_feriante)
    url = reverse('me-profile')
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == 'success'
    assert 'data' in response.data
    assert response.data['data']['user'] == str(user_feriante.id)


@pytest.mark.django_db
def test_get_me_profile_cliente(api_client, user_cliente):
    """Test GET /api/v1/me/ para usuario Cliente autenticado."""
    api_client.force_authenticate(user=user_cliente)
    url = reverse('me-profile')
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == 'success'
    assert 'direccion_entrega' in response.data['data']


@pytest.mark.django_db
def test_get_me_profile_repartidor(api_client, user_repartidor):
    """Test GET /api/v1/me/ para usuario Repartidor autenticado."""
    api_client.force_authenticate(user=user_repartidor)
    url = reverse('me-profile')
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == 'success'
    assert 'vehiculo' in response.data['data']
    assert 'licencia' in response.data['data']


@pytest.mark.django_db
def test_get_me_profile_unauthenticated(api_client):
    """Test GET /api/v1/me/ sin autenticación debe retornar 401."""
    url = reverse('me-profile')
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ========================================
# 🧪 TESTS DE ENDPOINT /me/ (PATCH)
# ========================================

@pytest.mark.django_db
def test_patch_me_profile_feriante(api_client, user_feriante):
    """Test PATCH /api/v1/me/ para actualizar perfil de Feriante."""
    api_client.force_authenticate(user=user_feriante)
    url = reverse('me-profile')
    
    data = {
        'rut': '12345678-9',
        'direccion': 'Av. Libertador 123',
        'puesto': 'Puesto 5-A'
    }
    
    response = api_client.patch(url, data, format='json')
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == 'success'
    assert response.data['data']['rut'] == '12345678-9'
    assert response.data['data']['direccion'] == 'Av. Libertador 123'


@pytest.mark.django_db
def test_patch_me_profile_cliente(api_client, user_cliente):
    """Test PATCH /api/v1/me/ para actualizar perfil de Cliente."""
    api_client.force_authenticate(user=user_cliente)
    url = reverse('me-profile')
    
    data = {
        'direccion_entrega': 'Calle Nueva 456'
    }
    
    response = api_client.patch(url, data, format='json')
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == 'success'
    assert response.data['data']['direccion_entrega'] == 'Calle Nueva 456'


@pytest.mark.django_db
def test_patch_me_profile_readonly_fields(api_client, user_feriante):
    """Test que los campos read-only no se puedan modificar."""
    api_client.force_authenticate(user=user_feriante)
    url = reverse('me-profile')
    
    original_created_at = FerianteProfile.objects.get(user=user_feriante).created_at
    
    data = {
        'created_at': '2020-01-01T00:00:00Z',  # Intentar modificar campo read-only
        'direccion': 'Nueva dirección'
    }
    
    response = api_client.patch(url, data, format='json')
    
    assert response.status_code == status.HTTP_200_OK
    perfil = FerianteProfile.objects.get(user=user_feriante)
    assert perfil.created_at == original_created_at  # No debe cambiar
    assert perfil.direccion == 'Nueva dirección'  # Sí debe cambiar


# ========================================
# 🧪 TESTS DE VALIDACIONES
# ========================================

@pytest.mark.django_db
def test_invalid_rut_format(api_client, user_feriante):
    """Test que valida formato de RUT chileno."""
    api_client.force_authenticate(user=user_feriante)
    url = reverse('me-profile')
    
    data = {
        'rut': '123456789'  # Formato inválido (sin guión ni dígito verificador)
    }
    
    response = api_client.patch(url, data, format='json')
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'rut' in response.data


@pytest.mark.django_db
def test_valid_rut_format(api_client, user_feriante):
    """Test que acepta RUT con formato válido."""
    api_client.force_authenticate(user=user_feriante)
    url = reverse('me-profile')
    
    data = {
        'rut': '12345678-9'  # Formato válido
    }
    
    response = api_client.patch(url, data, format='json')
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['data']['rut'] == '12345678-9'