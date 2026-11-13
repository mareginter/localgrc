import datetime
import uuid

from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .middleware import get_current_request, get_current_user
from .mixins import BaseModel
from .models import AuditLog


# Explicit tenant ownership paths for models that do not store organization
# directly. For link models, every path must resolve to the same organization.
_TENANT_RELATION_PATHS = {
    "audits.auditfinding": (("audit",),),
    "audits.correctiveaction": (("finding", "audit"),),
    "controls.controlrequirement": (("control",), ("requirement", "framework_version", "framework")),
    "controls.controlimplementation": (("control",),),
    "frameworks.frameworkversion": (("framework",),),
    "frameworks.requirement": (("framework_version", "framework"),),
    "incidents.regulatorydeadline": (("incident",),),
    "incidents.incidentasset": (("incident",), ("asset",)),
    "incidents.incidentvendor": (("incident",), ("vendor",)),
    "incidents.incidentrisk": (("incident",), ("risk",)),
    "policies.policyversion": (("policy",),),
    "policies.policyapproval": (("policy_version", "policy"),),
    "risks.riskassessment": (("risk",),),
    "risks.risktreatment": (("risk",),),
    "risks.riskasset": (("risk",), ("asset",)),
    "risks.riskcontrol": (("risk",), ("control",)),
    "vendors.vendorassessment": (("vendor",),),
    "vendors.vendorrisk": (("vendor",), ("risk",)),
    "vendors.vendorcontrol": (("vendor",), ("control",)),
}


def _serialize(instance):
    """Convert a model instance into a JSON-safe snapshot."""
    from decimal import Decimal

    def _safe(value):
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(
            value,
            (uuid.UUID, datetime.datetime, datetime.date, Decimal),
        ):
            return str(value)
        try:
            return str(value)
        except Exception:
            return repr(value)

    return {
        field.name: _safe(getattr(instance, field.attname, None))
        for field in instance._meta.fields
    }


def _diff(before, after, sender):
    """Compare business fields, excluding fields changed automatically on save.

    Full before/after snapshots retain timestamps for audit traceability.
    """
    automatic_fields = {
        field.name
        for field in sender._meta.fields
        if getattr(field, "auto_now", False)
    }
    return {
        key: {"before": before.get(key), "after": after[key]}
        for key in after
        if key not in automatic_fields and before.get(key) != after[key]
    }


def _org_id(instance):
    """Resolve tenant ownership using explicit, reviewed model relationships.

    Returning None is intentional when a relation is missing or when a link
    model connects records from different organizations: an audit event must
    never be attributed to an arbitrary tenant.
    """
    direct_org_id = getattr(instance, "organization_id", None)
    if direct_org_id is not None:
        return direct_org_id

    paths = _TENANT_RELATION_PATHS.get(instance._meta.label_lower, ())
    if not paths:
        return None

    resolved_ids = []
    for path in paths:
        related = instance
        try:
            for attribute in path:
                related = getattr(related, attribute)
            organization_id = getattr(related, "organization_id", None)
        except (AttributeError, ObjectDoesNotExist):
            return None
        if organization_id is None:
            return None
        resolved_ids.append(organization_id)

    # Link records must not silently bridge two tenants.
    return resolved_ids[0] if all(value == resolved_ids[0] for value in resolved_ids) else None


def _auditable(sender):
    return (
        issubclass(sender, BaseModel)
        and sender is not BaseModel
        and sender._meta.abstract is False
    )


def _audit_actor_and_request():
    request = get_current_request()
    user = get_current_user()
    if not getattr(user, "is_authenticated", False):
        user = None
    return request, user


@receiver(pre_save)
def audit_pre_save(sender, instance, **kwargs):
    if not _auditable(sender) or not instance.pk:
        return

    try:
        instance._audit_before = _serialize(
            sender.all_objects.get(pk=instance.pk)
        )
    except sender.DoesNotExist:
        instance._audit_before = None


@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    if not _auditable(sender):
        return

    if not created and not getattr(instance, "_audit_before", None):
        return

    after = _serialize(instance)
    before = None if created else instance._audit_before
    diff = None

    if before is not None:
        diff = _diff(before, after, sender)
        if not diff:
            return

    request, actor = _audit_actor_and_request()
    AuditLog.objects.create(
        organization_id=_org_id(instance),
        actor=actor,
        action=AuditLog.ACTION_CREATE if created else AuditLog.ACTION_UPDATE,
        entity_type=f"{sender._meta.app_label}.{sender._meta.model_name}",
        entity_id=instance.pk,
        before=before,
        after=after,
        diff=diff,
        ip=request.META.get("REMOTE_ADDR") if request else None,
        user_agent=request.META.get("HTTP_USER_AGENT", "") if request else "",
    )


@receiver(post_delete)
def audit_post_delete(sender, instance, **kwargs):
    if not _auditable(sender):
        return

    request, actor = _audit_actor_and_request()
    AuditLog.objects.create(
        organization_id=_org_id(instance),
        actor=actor,
        action=AuditLog.ACTION_DELETE,
        entity_type=f"{sender._meta.app_label}.{sender._meta.model_name}",
        entity_id=instance.pk,
        before=_serialize(instance),
        ip=request.META.get("REMOTE_ADDR") if request else None,
        user_agent=request.META.get("HTTP_USER_AGENT", "") if request else "",
    )
