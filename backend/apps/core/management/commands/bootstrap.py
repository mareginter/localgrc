import os

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core.models import Organization, Role, User, UserRole


class Command(BaseCommand):
    help = "Idempotent first-run bootstrap."

    @transaction.atomic
    def handle(self, *args, **opts):
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write("Bootstrap skipped â€” a superuser already exists.")
            return
        email = os.environ.get("LOCALGRC_ADMIN_EMAIL", "admin@local")
        password = os.environ.get("LOCALGRC_ADMIN_PASSWORD", "admin")
        org_name = os.environ.get("LOCALGRC_ADMIN_ORG_NAME", "Default Organization")
        org, _ = Organization.objects.get_or_create(slug="default", defaults={"name": org_name})
        user = User.objects.create_superuser(email=email, password=password)
        admin_role = Role.objects.get(code="admin")
        UserRole.objects.create(user=user, role=admin_role, organization=org)
        self.stdout.write(self.style.SUCCESS(
            f"Bootstrap complete. Login: {email} (change the password!)"
        ))
