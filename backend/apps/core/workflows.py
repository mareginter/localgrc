"""Tenant-safe helpers for reading and creating workflow instances."""

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction

from .models import WorkflowDefinition, WorkflowInstance


def _object_organization_id(obj):
    """Return the tenant id for supported workflow objects without guessing."""
    if obj._meta.label_lower == "core.organization":
        return obj.pk

    if any(field.name == "organization" for field in obj._meta.get_fields()):
        return getattr(obj, "organization_id", None)

    # AuditFinding is tenant-owned through its parent Audit.
    if any(field.name == "audit" for field in obj._meta.get_fields()):
        audit = getattr(obj, "audit", None)
        if audit is None or getattr(audit, "deleted_at", None) is not None:
            return None
        return getattr(audit, "organization_id", None)

    return None


def _validate_instance(instance, obj, organization, content_type):
    if instance.content_type_id != content_type.pk:
        raise PermissionDenied("Workflow entity type does not match the target object.")
    if instance.object_id != obj.pk:
        raise PermissionDenied("Workflow instance does not match the target object.")
    if instance.definition.content_type_id != content_type.pk:
        raise PermissionDenied("Workflow definition has an incompatible entity type.")
    if instance.definition.organization_id != organization.pk:
        raise PermissionDenied("Workflow belongs to another organization.")
    if instance.definition.deleted_at is not None:
        raise PermissionDenied("The workflow definition is inactive.")
    if getattr(obj, "deleted_at", None) is not None:
        raise PermissionDenied("A deleted object cannot use a workflow.")
    if instance.current_state.definition_id != instance.definition_id:
        raise PermissionDenied("Workflow current state belongs to another definition.")
    if _object_organization_id(obj) != organization.pk:
        raise PermissionDenied("The target object does not belong to the active organization.")


def _default_definition(organization, content_type):
    definitions = WorkflowDefinition.objects.filter(
        organization_id=organization.pk,
        content_type=content_type,
        is_default=True,
        deleted_at__isnull=True,
    ).order_by("created_at", "id")
    definition = definitions.first()
    if definition is not None and definitions.count() > 1:
        raise PermissionDenied("More than one default workflow is configured for this entity.")
    return definition


def _initial_state(definition, status, fallback_states=(), fallback_first=False):
    current_status = status or ""
    state = definition.states.filter(code=current_status).first() if current_status else None
    if state is None:
        for fallback_code in fallback_states:
            state = definition.states.filter(code=fallback_code).first()
            if state is not None:
                break
    if state is None and fallback_first:
        state = definition.states.order_by("order", "id").first()
    return state


def get_workflow_instance(
    obj,
    organization,
    *,
    status=None,
    fallback_states=(),
    fallback_first=False,
    create=False,
):
    """Read a validated workflow instance, optionally creating it for a POST.

    `create=False` is deliberately read-only and is suitable for detail-page GETs.
    """
    if obj is None or organization is None or not getattr(obj, "pk", None):
        raise PermissionDenied("A valid workflow object and organization are required.")
    if getattr(organization, "deleted_at", None) is not None:
        raise PermissionDenied("The workflow organization is not active.")

    content_type = ContentType.objects.get_for_model(obj, for_concrete_model=True)
    if _object_organization_id(obj) != organization.pk:
        raise PermissionDenied("The target object does not belong to the active organization.")

    queryset = WorkflowInstance.objects.select_related("definition", "current_state")
    instance = queryset.filter(content_type=content_type, object_id=obj.pk).first()
    if instance is not None:
        _validate_instance(instance, obj, organization, content_type)
        return instance

    if not create:
        return None

    definition = _default_definition(organization, content_type)
    if definition is None:
        return None

    current_status = status if status is not None else getattr(obj, "status", "")
    state = _initial_state(definition, current_status, fallback_states, fallback_first)
    if state is None:
        return None

    try:
        with transaction.atomic():
            instance = WorkflowInstance.objects.create(
                definition=definition,
                content_type=content_type,
                object_id=obj.pk,
                current_state=state,
            )
    except IntegrityError:
        # A concurrent POST may have created the unique instance first.
        instance = queryset.get(content_type=content_type, object_id=obj.pk)

    _validate_instance(instance, obj, organization, content_type)
    return instance


def get_workflow_transitions(
    obj,
    organization,
    *,
    status=None,
    fallback_states=(),
    fallback_first=False,
):
    """Return available transitions without creating a WorkflowInstance."""
    instance = get_workflow_instance(
        obj,
        organization,
        status=status,
        fallback_states=fallback_states,
        fallback_first=fallback_first,
        create=False,
    )
    if instance is not None:
        current_state = instance.current_state
    else:
        content_type = ContentType.objects.get_for_model(obj, for_concrete_model=True)
        definition = _default_definition(organization, content_type)
        if definition is None:
            return []
        current_status = status if status is not None else getattr(obj, "status", "")
        current_state = _initial_state(
            definition, current_status, fallback_states, fallback_first
        )
        if current_state is None:
            return []

    return list(
        current_state.outgoing.filter(
            definition_id=current_state.definition_id,
            to_state__definition_id=current_state.definition_id,
        ).select_related("to_state")
    )
