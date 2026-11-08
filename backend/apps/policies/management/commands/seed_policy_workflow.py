from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from apps.core.models import Organization, Role, WorkflowDefinition, WorkflowInstance, WorkflowState, WorkflowTransition
from apps.policies.models import Policy


STATES = [
    ("draft", "Draft", False, 1),
    ("in_review", "In review", False, 2),
    ("approved", "Approved", False, 3),
    ("published", "Published", False, 4),
    ("retired", "Retired", True, 5),
]

TRANSITIONS = [
    ("draft", "in_review", "contributor"),
    ("in_review", "approved", "risk_manager"),
    ("in_review", "draft", "risk_manager"),
    ("approved", "published", "risk_manager"),
    ("published", "retired", "risk_manager"),
]


class Command(BaseCommand):
    help = "Seed the Policy workflow definition + backfill instances."

    def handle(self, *args, **opts):
        ct = ContentType.objects.get_for_model(Policy)
        for org in Organization.objects.all():
            defn, created = WorkflowDefinition.objects.get_or_create(
                organization=org, content_type=ct, name="Policy lifecycle",
                defaults={"is_default": True},
            )
            if created:
                self.stdout.write(f"Created Policy workflow for {org.slug}")
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
            for policy in Policy.objects.filter(organization=org):
                state = states.get(policy.status) or states["draft"]
                _, c = WorkflowInstance.objects.get_or_create(
                    content_type=ct, object_id=policy.pk,
                    defaults={"definition": defn, "current_state": state},
                )
                if c:
                    backfilled += 1
            self.stdout.write(self.style.SUCCESS(
                f"[{org.slug}] Policy workflow ready, {backfilled} instances backfilled"
            ))