import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied, ValidationError

from apps.core.models import (
    AuditLog, Organization, Role, UserRole, WorkflowDefinition,
    WorkflowInstance, WorkflowState, WorkflowTransition,
)
from apps.core.workflows import get_workflow_instance, get_workflow_transitions


@pytest.fixture
def workflow(db, org, user):
    ct = ContentType.objects.get_for_model(Organization)
    definition = WorkflowDefinition.objects.create(
        organization=org,
        content_type=ct,
        name="Default",
        is_default=True,
    )
    draft = WorkflowState.objects.create(
        definition=definition, code="draft", label="Draft", order=1
    )
    approved = WorkflowState.objects.create(
        definition=definition, code="approved", label="Approved", order=2
    )
    transition = WorkflowTransition.objects.create(
        definition=definition,
        from_state=draft,
        to_state=approved,
        required_role=Role.objects.get(code="admin"),
    )
    instance = WorkflowInstance.objects.create(
        definition=definition,
        content_type=ct,
        object_id=org.pk,
        current_state=draft,
    )
    return draft, approved, instance, transition


def test_transition_allowed(workflow, user):
    _, approved, instance, _ = workflow
    instance.transition(user, approved, comment="ok")
    instance.refresh_from_db()
    assert instance.current_state.code == "approved"


def test_transition_denied_without_role(workflow):
    from django.contrib.auth import get_user_model

    stranger = get_user_model().objects.create_user(
        email="stranger@test.local", password="pass1234word!"
    )
    _, approved, instance, _ = workflow
    with pytest.raises(PermissionDenied):
        instance.transition(stranger, approved)


def test_membership_is_required_even_when_transition_has_no_required_role(workflow):
    from django.contrib.auth import get_user_model

    stranger = get_user_model().objects.create_user(
        email="no-membership@test.local", password="pass1234word!"
    )
    _, approved, instance, transition = workflow
    transition.required_role = None
    transition.save(update_fields=["required_role"])

    with pytest.raises(PermissionDenied, match="not a member"):
        instance.transition(stranger, approved)


def test_membership_in_another_organization_is_not_enough(workflow):
    from django.contrib.auth import get_user_model

    other_org = Organization.objects.create(name="Other", slug="other-workflow-org")
    stranger = get_user_model().objects.create_user(
        email="other-org@test.local", password="pass1234word!"
    )
    UserRole.objects.create(
        user=stranger,
        role=Role.objects.get(code="admin"),
        organization=other_org,
    )
    _, approved, instance, _ = workflow

    with pytest.raises(PermissionDenied, match="not a member"):
        instance.transition(stranger, approved)


def test_superuser_does_not_bypass_tenant_membership(workflow):
    from django.contrib.auth import get_user_model

    superuser = get_user_model().objects.create_superuser(
        email="platform@test.local", password="pass1234word!"
    )
    _, approved, instance, _ = workflow

    with pytest.raises(PermissionDenied, match="not a member"):
        instance.transition(superuser, approved)


def test_superuser_with_tenant_membership_bypasses_only_required_role(workflow, org):
    from django.contrib.auth import get_user_model

    superuser = get_user_model().objects.create_superuser(
        email="platform-member@test.local", password="pass1234word!"
    )
    UserRole.objects.create(
        user=superuser,
        role=Role.objects.get(code="reader"),
        organization=org,
    )
    _, approved, instance, _ = workflow

    instance.transition(superuser, approved)
    instance.refresh_from_db()
    assert instance.current_state == approved


def test_target_state_from_another_definition_is_rejected(workflow, org, user):
    _, _, instance, _ = workflow
    ct = ContentType.objects.get_for_model(Organization)
    other_definition = WorkflowDefinition.objects.create(
        organization=org, content_type=ct, name="Other workflow"
    )
    foreign_state = WorkflowState.objects.create(
        definition=other_definition, code="foreign", label="Foreign"
    )

    with pytest.raises(PermissionDenied, match="target state"):
        instance.transition(user, foreign_state)


def test_workflow_instance_for_wrong_tenant_is_rejected_by_lookup(db):
    target_org = Organization.objects.create(name="Target", slug="target-org")
    other_org = Organization.objects.create(name="Other", slug="wrong-workflow-org")
    ct = ContentType.objects.get_for_model(Organization)
    definition = WorkflowDefinition.objects.create(
        organization=other_org, content_type=ct, name="Foreign default", is_default=True
    )
    state = WorkflowState.objects.create(
        definition=definition, code="draft", label="Draft"
    )
    # The workflow row points to the target object but is owned by another tenant.
    WorkflowInstance.objects.create(
        definition=definition,
        content_type=ct,
        object_id=target_org.pk,
        current_state=state,
    )

    with pytest.raises(PermissionDenied, match="another organization"):
        get_workflow_instance(target_org, target_org, create=False)


def test_read_only_workflow_lookup_does_not_create_instance(org):
    ct = ContentType.objects.get_for_model(Organization)
    definition = WorkflowDefinition.objects.create(
        organization=org, content_type=ct, name="Read only default", is_default=True
    )
    draft = WorkflowState.objects.create(definition=definition, code="draft", label="Draft")
    approved = WorkflowState.objects.create(
        definition=definition, code="approved", label="Approved"
    )
    WorkflowTransition.objects.create(
        definition=definition, from_state=draft, to_state=approved
    )

    assert get_workflow_instance(org, org, status="draft", create=False) is None
    transitions = get_workflow_transitions(org, org, status="draft")
    assert len(transitions) == 1
    assert transitions[0].to_state == approved
    assert WorkflowInstance.objects.filter(content_type=ct, object_id=org.pk).count() == 0

    instance = get_workflow_instance(org, org, status="draft", create=True)
    assert instance is not None
    assert WorkflowInstance.objects.filter(content_type=ct, object_id=org.pk).count() == 1


def test_required_comment_is_enforced(workflow, user):
    _, approved, instance, transition = workflow
    transition.requires_comment = True
    transition.save(update_fields=["requires_comment"])

    with pytest.raises(ValidationError, match="comment is required"):
        instance.transition(user, approved, comment="   ")

    instance.refresh_from_db()
    assert instance.current_state.code == "draft"

    instance.transition(user, approved, comment="Approved after review")
    instance.refresh_from_db()
    assert instance.current_state.code == "approved"


def test_transition_and_audit_are_atomic(workflow, user, monkeypatch):
    _, approved, instance, _ = workflow

    def fail_save(*args, **kwargs):
        raise RuntimeError("simulated audit write failure")

    monkeypatch.setattr(AuditLog, "save", fail_save)
    with pytest.raises(RuntimeError, match="audit write failure"):
        instance.transition(user, approved, comment="ok")

    instance.refresh_from_db()
    assert instance.current_state.code == "draft"


def test_current_state_from_another_definition_is_rejected(workflow, org, user):
    _, approved, instance, _ = workflow
    ct = ContentType.objects.get_for_model(Organization)
    other_definition = WorkflowDefinition.objects.create(
        organization=org, content_type=ct, name="Mismatched current state"
    )
    foreign_state = WorkflowState.objects.create(
        definition=other_definition, code="foreign-current", label="Foreign current"
    )
    instance.current_state = foreign_state
    instance.save(update_fields=["current_state"])

    with pytest.raises(PermissionDenied, match="current state"):
        instance.transition(user, approved)


def test_deleted_organization_cannot_resolve_workflow(org):
    from django.utils import timezone

    org.deleted_at = timezone.now()
    org.save(update_fields=["deleted_at", "updated_at"])

    with pytest.raises(PermissionDenied, match="organization is not active"):
        get_workflow_instance(org, org, create=False)


def test_deleted_default_definition_is_not_used_for_creation(org):
    from django.utils import timezone

    ct = ContentType.objects.get_for_model(Organization)
    definition = WorkflowDefinition.objects.create(
        organization=org, content_type=ct, name="Deleted default", is_default=True
    )
    definition.deleted_at = timezone.now()
    definition.save(update_fields=["deleted_at", "updated_at"])
    WorkflowState.objects.create(definition=definition, code="draft", label="Draft")

    assert get_workflow_instance(org, org, status="draft", create=True) is None
    assert WorkflowInstance.objects.filter(content_type=ct, object_id=org.pk).count() == 0


def test_transition_listing_excludes_mismatched_definition_rows(workflow, org):
    draft, approved, _instance, expected_transition = workflow
    ct = ContentType.objects.get_for_model(Organization)
    other_definition = WorkflowDefinition.objects.create(
        organization=org, content_type=ct, name="Foreign transition definition"
    )
    WorkflowTransition.objects.create(
        definition=other_definition,
        from_state=draft,
        to_state=approved,
    )

    transitions = get_workflow_transitions(org, org, status="draft")

    assert transitions == [expected_transition]


def test_tenant_member_without_required_role_is_denied(workflow, org):
    from django.contrib.auth import get_user_model

    reader = get_user_model().objects.create_user(
        email="workflow-reader@test.local", password="pass1234word!"
    )
    UserRole.objects.create(
        user=reader,
        role=Role.objects.get(code="reader"),
        organization=org,
    )
    _, approved, instance, _ = workflow

    with pytest.raises(PermissionDenied, match="role required"):
        instance.transition(reader, approved)
