from django.core.management.base import BaseCommand

from apps.controls.models import Control, ControlRequirement
from apps.core.models import Organization
from apps.frameworks.models import FrameworkVersion, Requirement


SAMPLE_CONTROLS = [
    {
        "name": "Access control policy",
        "description": "Documented policy defining access control rules and responsibilities.",
        "control_type": "preventive",
        "category": "Access Control",
        "iso": ["A.5.15", "A.5.18"],
    },
    {
        "name": "Multi-factor authentication",
        "description": "MFA enforced for all users accessing production systems.",
        "control_type": "preventive",
        "category": "Authentication",
        "iso": ["A.5.17", "A.8.5"],
    },
    {
        "name": "Logging and monitoring",
        "description": "Centralized logging of security events with alerting.",
        "control_type": "detective",
        "category": "Monitoring",
        "iso": ["A.8.15", "A.8.16"],
    },
    {
        "name": "Backup and restore",
        "description": "Regular backups with tested restore procedures.",
        "control_type": "corrective",
        "category": "Resilience",
        "iso": ["A.8.13"],
    },
    {
        "name": "Incident response plan",
        "description": "Documented incident response plan with defined roles.",
        "control_type": "corrective",
        "category": "Incident Management",
        "iso": ["A.5.24", "A.5.26"],
    },
]


class Command(BaseCommand):
    help = "Seed sample controls mapped to ISO 27001 requirements. Idempotent."

    def handle(self, *args, **opts):
        org = Organization.objects.first()
        if not org:
            self.stdout.write(self.style.ERROR("No organization found."))
            return

        iso_version = FrameworkVersion.objects.filter(
            framework__organization=org, framework__code="iso27001", is_active=True
        ).first()
        if not iso_version:
            self.stdout.write(self.style.ERROR(
                "ISO 27001 not seeded. Run 'python manage.py seed_frameworks' first."
            ))
            return

        created = 0
        for spec in SAMPLE_CONTROLS:
            control, was_created = Control.objects.get_or_create(
                organization=org,
                name=spec["name"],
                defaults={
                    "description": spec["description"],
                    "control_type": spec["control_type"],
                    "category": spec["category"],
                    "status": "approved",
                },
            )
            if was_created:
                created += 1
            for req_code in spec["iso"]:
                req = Requirement.objects.filter(
                    framework_version=iso_version, code=req_code
                ).first()
                if req:
                    ControlRequirement.objects.get_or_create(
                        control=control, requirement=req,
                        defaults={"coverage": "full"},
                    )
        self.stdout.write(self.style.SUCCESS(
            f"Seeded {created} new controls (total sample controls mapped to ISO 27001)."
        ))