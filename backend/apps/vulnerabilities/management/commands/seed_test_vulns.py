from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from apps.vulnerabilities.models import Vulnerability
from apps.core.models import Organization

class Command(BaseCommand):
    help = "Lists current vulnerabilities and creates test data."

    def add_arguments(self, parser):
        parser.add_argument("--organization", required=True, help="Organization slug to seed.")

    def handle(self, *args, **kwargs):
        try:
            organization = Organization.objects.get(slug=kwargs["organization"])
        except Organization.DoesNotExist as exc:
            raise CommandError("Organization not found. Provide a valid --organization slug.") from exc
        User = get_user_model()
        admin_user = User.objects.filter(
            user_roles__organization=organization,
            user_roles__role__code="admin",
            user_roles__deleted_at__isnull=True,
        ).distinct().first()

        # 1. VER O QUE JÁ EXISTE
        qs = Vulnerability.objects.filter(organization=organization)
        count = qs.count()
        self.stdout.write(self.style.WARNING(f"Existem atualmente {count} vulnerabilidades registadas na base de dados."))

        if count > 0:
            self.stdout.write("\nÚltimas vulnerabilidades registadas:")
            for v in qs.order_by('-discovered_at')[:5]:
                self.stdout.write(f" - [{v.severity.upper()}] {v.title} ({v.status})")

        # 2. CRIAR DADOS DE TESTE (Se não existirem)
        if not qs.filter(title="Missing MFA on Admin Portal").exists():
            self.stdout.write("\nA criar vulnerabilidades de teste...")
            today = timezone.now().date()

            # Teste 1: Crítica e Atrasada (Overdue)
            Vulnerability.objects.create(
                organization=organization,
                title="Missing MFA on Admin Portal",
                description="The administrative login portal does not enforce Multi-Factor Authentication, allowing brute-force attacks.",
                affected_endpoint="https://admin.localgrc.local/login",
                severity="critical",
                cvss_score=9.8,
                status="open",
                remediation_plan="Implement TOTP-based MFA for all admin users.",
                due_date=today - timedelta(days=2), # Data no passado para ficar vermelho
                owner=admin_user
            )
            self.stdout.write(self.style.SUCCESS("  [+] Criada: Missing MFA (Critical, Overdue)"))

            # Teste 2: Alta e em Progresso
            Vulnerability.objects.create(
                organization=organization,
                title="Outdated Apache Web Server",
                cve_id="CVE-2021-41773",
                description="Path traversal and remote code execution vulnerability in Apache HTTP Server 2.4.49.",
                affected_endpoint="192.168.1.50 (Internal Web Server)",
                severity="high",
                cvss_score=7.5,
                status="in_progress",
                remediation_plan="Upgrade Apache to version 2.4.51 or higher.",
                due_date=today + timedelta(days=10),
                owner=admin_user
            )
            self.stdout.write(self.style.SUCCESS("  [+] Criada: Outdated Apache (High, In Progress)"))

            # Teste 3: Média
            Vulnerability.objects.create(
                organization=organization,
                title="Directory Listing Enabled",
                description="The API documentation folder allows directory listing, exposing internal endpoints.",
                affected_endpoint="https://api.localgrc.local/docs/",
                severity="medium",
                cvss_score=5.3,
                status="open",
                remediation_plan="Disable directory listing in Nginx configuration (autoindex off).",
                due_date=today + timedelta(days=30),
                owner=admin_user
            )
            self.stdout.write(self.style.SUCCESS("  [+] Criada: Directory Listing (Medium, Open)"))
            
            self.stdout.write(self.style.SUCCESS("\nConcluído! Vai ao Dashboard para ver o resultado."))
        else:
            self.stdout.write(self.style.SUCCESS("\nAs vulnerabilidades de teste já existem."))
