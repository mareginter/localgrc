from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from apps.core.models import Organization, Role, WorkflowDefinition, WorkflowInstance, WorkflowState, WorkflowTransition
from apps.vendors.models import Vendor


STATES = [
    ("active", "Active", False, 1),
    ("under_review", "Under review", False, 2),
    ("terminated", "Terminated", True, 3),
]
TRANSITIONS = [
    ("active", "under_review", "risk_manager"),
    ("under_review", "active", "risk_manager"),
    ("active", "terminated", "risk_manager"),
    ("under_review", "terminated", "risk_manager"),
]


class Command(BaseCommand):
    help = "Seed Vendor workflow definition + backfill."

    def handle(self, *args, **opts):
        ct = ContentType.objects.get_for_model(Vendor)
        for org in Organization.objects.all():
            defn, created = WorkflowDefinition.objects.get_or_create(
                organization=org, content_type=ct, name="Vendor lifecycle",
                defaults={"is_default": True},
            )
            if created:
                self.stdout.write(f"Created Vendor workflow for {org.slug}")
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
            backfilled = 0
            for v in Vendor.objects.filter(organization=org):
                state = states.get(v.status) or states["active"]
                _, c = WorkflowInstance.objects.get_or_create(
                    content_type=ct, object_id=v.pk,
                    defaults={"definition": defn, "current_state": state},
                )
                if c:
                    backfilled += 1
            self.stdout.write(self.style.SUCCESS(
                f"[{org.slug}] Vendor workflow ready, {backfilled} instances backfilled"
            ))