from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from apps.core.models import Organization, Role, WorkflowDefinition, WorkflowState, WorkflowTransition
from apps.risks.models import Risk


STATES = [
    ("draft", "Draft", False, 1),
    ("under_review", "Under review", False, 2),
    ("approved", "Approved", False, 3),
    ("rejected", "Rejected", True, 4),
    ("mitigating", "Mitigating", False, 5),
    ("closed", "Closed", True, 6),
]

TRANSITIONS = [
    ("draft", "under_review", "contributor"),
    ("under_review", "approved", "risk_manager"),
    ("under_review", "rejected", "risk_manager"),
    ("approved", "mitigating", "risk_manager"),
    ("mitigating", "closed", "risk_manager"),
]


class Command(BaseCommand):
    help = "Seed the Risk workflow definition (idempotent)."

    def handle(self, *args, **opts):
        ct = ContentType.objects.get_for_model(Risk)
        for org in Organization.objects.all():
            defn, created = WorkflowDefinition.objects.get_or_create(
                organization=org, content_type=ct, name="Risk lifecycle",
                defaults={"is_default": True},
            )
            if created:
                self.stdout.write(f"Created workflow definition for {org.slug}")
            states = {}
            for code, label, terminal, order in STATES:
                s, _ = WorkflowState.objects.get_or_create(
                    definition=defn, code=code,
                    defaults={"label": label, "is_terminal": terminal, "order": order},
                )
                states[code] = s
            for from_c, to_c, role_code in TRANSITIONS:
                try:
                    role = Role.objects.get(code=role_code)
                except Role.DoesNotExist:
                    role = None
                WorkflowTransition.objects.get_or_create(
                    definition=defn,
                    from_state=states[from_c],
                    to_state=states[to_c],
                    defaults={"required_role": role},
                )
            self.stdout.write(self.style.SUCCESS(f"Workflow ready for {org.slug}"))