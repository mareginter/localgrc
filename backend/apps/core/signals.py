import datetime
import uuid

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .middleware import get_current_request, get_current_user
from .mixins import BaseModel
from .models import AuditLog


def _serialize(instance):
    data = {}
    for field in instance._meta.fields:
        value = getattr(instance, field.attname, None)
        if isinstance(value, (uuid.UUID, datetime.datetime, datetime.date)):
            value = str(value)
        data[field.name] = value
    return data


def _org_id(instance):
    org = getattr(instance, "organization", None)
    return getattr(org, "pk", None)


def _auditable(sender):
    return (
        issubclass(sender, BaseModel)
        and sender is not BaseModel
        and sender._meta.abstract is False
    )


@receiver(pre_save)
def audit_pre_save(sender, instance, **kwargs):
    if not _auditable(sender) or not instance.pk:
        return
    try:
        instance._audit_before = _serialize(sender.all_objects.get(pk=instance.pk))
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
        diff = {k: {"before": before[k], "after": after[k]}
                for k in after if before.get(k) != after[k]}
        if not diff:
            return
    request = get_current_request()
    AuditLog.objects.create(
        organization_id=_org_id(instance),
        actor=get_current_user() if getattr(get_current_user(), "is_authenticated", False) else None,
        action=AuditLog.ACTION_CREATE if created else AuditLog.ACTION_UPDATE,
        entity_type=f"{sender._meta.app_label}.{sender._meta.model_name}",
        entity_id=instance.pk,
        before=before, after=after, diff=diff,
        ip=(request.META.get("REMOTE_ADDR") if request else None),
        user_agent=(request.META.get("HTTP_USER_AGENT", "") if request else ""),
    )


@receiver(post_delete)
def audit_post_delete(sender, instance, **kwargs):
    if not _auditable(sender):
        return
    request = get_current_request()
    AuditLog.objects.create(
        organization_id=_org_id(instance),
        actor=get_current_user() if getattr(get_current_user(), "is_authenticated", False) else None,
        action=AuditLog.ACTION_DELETE,
        entity_type=f"{sender._meta.app_label}.{sender._meta.model_name}",
        entity_id=instance.pk,
        before=_serialize(instance),
        ip=(request.META.get("REMOTE_ADDR") if request else None),
        user_agent=(request.META.get("HTTP_USER_AGENT", "") if request else ""),
    )
