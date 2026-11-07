from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from apps.controls.models import Control
from apps.core.models import Organization, Role, WorkflowDefinition, WorkflowInstance, WorkflowState, WorkflowTransition


STATES = [
    ("draft", "Draft", False, 1),
    ("approved", "Approved", False, 2),
    ("implemented", "Implemented", False, 3),
    ("retired", "Retired", True, 4),
]

TRANSITIONS = [
    ("draft", "approved", "risk_manager"),
    ("approved", "implemented", "control_owner"),
    ("implemented", "retired", "risk_manager"),
]


class Command(BaseCommand):
    help = "Seed the Control workflow definition + instances for existing controls."

    def handle(self, *args, **opts):
        ct = ContentType.objects.get_for_model(Control)
        for org in Organization.objects.all():
            defn, created = WorkflowDefinition.objects.get_or_create(
                organization=org, content_type=ct, name="Control lifecycle",
                defaults={"is_default": True},
            )
            if created:
                self.stdout.write(f"Created Control workflow for {org.slug}")
            states = {}
            for code, label, terminal, order in STATES:
                s, _ = WorkflowState.objects.get_or_create(
                    definition=defn, code=code,
                    defaults={"label": label, "is_terminal": terminal, "order": order},
                )
                states[code] = s
            for from_c, to_c, role_code in TRANSITIONS:
                role = Role.objects.filter(code=role_code).first()
                WorkflowTransition.objects.get_or_create(
                    definition=defn,
                    from_state=states[from_c],
                    to_state=states[to_c],
                    defaults={"required_role": role},
                )
            # Backfill instances for existing controls without one
            backfilled = 0
            for control in Control.objects.filter(organization=org):
                state = states.get(control.status) or states["draft"]
                _, created = WorkflowInstance.objects.get_or_create(
                    content_type=ct, object_id=control.pk,
                    defaults={"definition": defn, "current_state": state},
                )
                if created:
                    backfilled += 1
            self.stdout.write(self.style.SUCCESS(
                f"[{org.slug}] Control workflow ready, {backfilled} instances backfilled"
            ))