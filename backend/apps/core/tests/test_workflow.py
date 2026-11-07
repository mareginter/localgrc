import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied

from apps.core.models import (
    Organization, Role, WorkflowDefinition, WorkflowInstance,
    WorkflowState, WorkflowTransition,
)


@pytest.fixture
def workflow(db, org, user):
    ct = ContentType.objects.get_for_model(Organization)
    d = WorkflowDefinition.objects.create(organization=org, content_type=ct,
                                          name="Default", is_default=True)
    draft = WorkflowState.objects.create(definition=d, code="draft", label="Draft", order=1)
    approved = WorkflowState.objects.create(definition=d, code="approved", label="Approved", order=2)
    WorkflowTransition.objects.create(definition=d, from_state=draft, to_state=approved,
                                     required_role=Role.objects.get(code="admin"))
    inst = WorkflowInstance.objects.create(definition=d, content_type=ct,
                                          object_id=org.pk, current_state=draft)
    return draft, approved, inst


def test_transition_allowed(workflow, user):
    _, approved, inst = workflow
    inst.transition(user, approved, comment="ok")
    assert inst.current_state.code == "approved"


def test_transition_denied_without_role(workflow):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    stranger = User.objects.create_user(email="stranger@test.local", password="pass1234word!")
    _, approved, inst = workflow
    with pytest.raises(PermissionDenied):
        inst.transition(stranger, approved)
