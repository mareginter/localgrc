import pytest
from django.contrib.auth import get_user_model

from apps.core.models import Organization, Role, UserRole


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Test Org", slug="test-org")


@pytest.fixture
def user(db, org):
    user_model = get_user_model()
    user = user_model.objects.create_user(
        email="user@test.local",
        password="pass1234word!",
    )
    admin_role = Role.objects.get(code="admin")
    UserRole.objects.create(user=user, role=admin_role, organization=org)
    return user
