from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from apps.audits.models import Audit, AuditFinding
from apps.core.models import Organization, Role, WorkflowDefinition, WorkflowInstance, WorkflowState, WorkflowTransition


AUDIT_STATES = [
    ("planned", "Planned", False, 1),
    ("in_progress", "In progress", False, 2),
    ("completed", "Completed", True, 3),
    ("cancelled", "Cancelled", True, 4),
]
AUDIT_TRANSITIONS = [
    ("planned", "in_progress", "auditor"),
    ("in_progress", "completed", "auditor"),
    ("planned", "cancelled", "risk_manager"),
]

FINDING_STATES = [
    ("open", "Open", False, 1),
    ("in_progress", "In progress", False, 2),
    ("resolved", "Resolved", False, 3),
    ("verified", "Verified", False, 4),
    ("closed", "Closed", True, 5),
]
FINDING_TRANSITIONS = [
    ("open", "in_progress", "contributor"),
    ("in_progress", "resolved", "control_owner"),
    ("resolved", "verified", "auditor"),
    ("verified", "closed", "auditor"),
    ("open", "closed", "auditor"),
]


class Command(BaseCommand):
    help = "Seed workflows for Audit and AuditFinding."

    def handle(self, *args, **opts):
        for org in Organization.objects.all():
            self._seed(org, Audit, "Audit lifecycle", AUDIT_STATES, AUDIT_TRANSITIONS)
            self._seed(org, AuditFinding, "Finding lifecycle", FINDING_STATES, FINDING_TRANSITIONS)

    def _seed(self, org, model, name, states, transitions):
        ct = ContentType.objects.get_for_model(model)
        defn, created = WorkflowDefinition.objects.get_or_create(
            organization=org, content_type=ct, name=name,
            defaults={"is_default": True},
        )
        if created:
            self.stdout.write(f"Created workflow '{name}' for {org.slug}")
        state_map = {}
        for code, label, terminal, order in states:
            s, _ = WorkflowState.objects.get_or_create(
                definition=defn, code=code,
                defaults={"label": label, "is_terminal": terminal, "order": order},
            )
            state_map[code] = s
        for from_c, to_c, role_code in transitions:
            role = Role.objects.filter(code=role_code).first()
            WorkflowTransition.objects.get_or_create(
                definition=defn,
                from_state=state_map[from_c],
                to_state=state_map[to_c],
                defaults={"required_role": role},
            )
        backfilled = 0
        if model is AuditFinding:
            objects = model.objects.filter(audit__organization=org)
        else:
            objects = model.objects.filter(organization=org)
        for obj in objects:
            state = state_map.get(getattr(obj, "status", "planned")) or state_map[list(state_map)[0]]
            _, c = WorkflowInstance.objects.get_or_create(
                content_type=ct, object_id=obj.pk,
                defaults={"definition": defn, "current_state": state},
            )
            if c:
                backfilled += 1
        self.stdout.write(self.style.SUCCESS(
            f"[{org.slug}] {name} ready, {backfilled} instances backfilled"
        ))