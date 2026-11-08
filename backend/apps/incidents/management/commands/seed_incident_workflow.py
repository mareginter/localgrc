from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from apps.core.models import Organization, Role, WorkflowDefinition, WorkflowInstance, WorkflowState, WorkflowTransition
from apps.incidents.models import Incident


STATES = [
    ("detected", "Detected", False, 1),
    ("triaged", "Triaged", False, 2),
    ("contained", "Contained", False, 3),
    ("eradicated", "Eradicated", False, 4),
    ("recovered", "Recovered", False, 5),
    ("closed", "Closed", True, 6),
]
TRANSITIONS = [
    ("detected", "triaged", "contributor"),
    ("triaged", "contained", "contributor"),
    ("contained", "eradicated", "contributor"),
    ("eradicated", "recovered", "contributor"),
    ("recovered", "closed", "risk_manager"),
    ("triaged", "closed", "risk_manager"),
]


class Command(BaseCommand):
    help = "Seed Incident workflow definition + backfill."

    def handle(self, *args, **opts):
        ct = ContentType.objects.get_for_model(Incident)
        for org in Organization.objects.all():
            defn, created = WorkflowDefinition.objects.get_or_create(
                organization=org, content_type=ct, name="Incident lifecycle",
                defaults={"is_default": True},
            )
            if created:
                self.stdout.write(f"Created Incident workflow for {org.slug}")
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
            for inc in Incident.objects.filter(organization=org):
                state = states.get(inc.status) or states["detected"]
                _, c = WorkflowInstance.objects.get_or_create(
                    content_type=ct, object_id=inc.pk,
                    defaults={"definition": defn, "current_state": state},
                )
                if c:
                    backfilled += 1
            self.stdout.write(self.style.SUCCESS(
                f"[{org.slug}] Incident workflow ready, {backfilled} instances backfilled"
            ))