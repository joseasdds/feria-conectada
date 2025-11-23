import pytest

from users.models import Role, User


@pytest.mark.django_db
def test_create_user_with_role():
    role = Role.objects.create(name="FERIANTE")
    user = User.objects.create_user(
        email="test@feria.cl", password="1234", full_name="Test User", role=role
    )
    assert user.email == "test@feria.cl"
    assert user.role.name == "FERIANTE"
    assert user.check_password("1234")
