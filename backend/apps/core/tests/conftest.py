import pytest
from django.contrib.auth import get_user_model
from apps.core.models import Organization, Role, UserRole

User = get_user_model()


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Test Org", slug="test-org")


@pytest.fixture
def user(db, org):
    u = User.objects.create_user(email="user@test.local", password="pass1234word!")
    UserRole.objects.create(user=u, role=Role.objects.get(code="admin"), organization=org)
    return u
