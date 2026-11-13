from datetime import date

from django.core.management.base import BaseCommand

from apps.core.models import Organization
from apps.frameworks.models import Framework, FrameworkVersion, Requirement


SOC2_CONTROLS = [
    ("CC1", "Control Environment", "Common Criteria"),
    ("CC2", "Communication and Information", "Common Criteria"),
    ("CC3", "Risk Assessment", "Common Criteria"),
    ("CC4", "Monitoring Activities", "Common Criteria"),
    ("CC5", "Control Activities", "Common Criteria"),
    ("CC6", "Logical and Physical Access Controls", "Common Criteria"),
    ("CC7", "System Operations", "Common Criteria"),
    ("CC8", "Change Management", "Common Criteria"),
    ("CC9", "Risk Mitigation", "Common Criteria"),
    ("A1", "Availability", "Availability"),
    ("C1", "Confidentiality", "Confidentiality"),
    ("PI1", "Processing Integrity", "Processing Integrity"),
    ("P1", "Privacy", "Privacy"),
]

GDPR_ARTICLES = [
    ("Art.5", "Principles relating to processing of personal data", "Core principles"),
    ("Art.6", "Lawfulness of processing", "Lawful basis"),
    ("Art.7", "Conditions for consent", "Consent"),
    ("Art.12", "Transparent information and communication", "Transparency"),
    ("Art.13", "Information to be provided where data is collected", "Transparency"),
    ("Art.14", "Information to be provided where data not obtained", "Transparency"),
    ("Art.15", "Right of access by the data subject", "Data subject rights"),
    ("Art.16", "Right to rectification", "Data subject rights"),
    ("Art.17", "Right to erasure (right to be forgotten)", "Data subject rights"),
    ("Art.18", "Right to restriction of processing", "Data subject rights"),
    ("Art.20", "Right to data portability", "Data subject rights"),
    ("Art.24", "Responsibility of the controller", "Governance"),
    ("Art.25", "Data protection by design and by default", "Governance"),
    ("Art.28", "Processor obligations", "Third parties"),
    ("Art.30", "Records of processing activities", "Documentation"),
    ("Art.32", "Security of processing", "Security"),
    ("Art.33", "Notification of a personal data breach to the supervisory authority", "Breach"),
    ("Art.34", "Communication of a personal data breach to the data subject", "Breach"),
    ("Art.35", "Data protection impact assessment (DPIA)", "Assessment"),
    ("Art.37", "Designation of the data protection officer (DPO)", "Governance"),
]

NIS2_ARTICLES = [
    ("Art.20", "Governance - management body obligations", "Governance"),
    ("Art.21", "Cybersecurity risk-management measures", "Risk management"),
    ("Art.23", "Reporting obligations - incident notification", "Incidents"),
    ("Art.24", "Use of European cybersecurity certification schemes", "Certification"),
    ("Art.25", "Standardization", "Standards"),
    ("Art.27", "Cybersecurity training and exercises", "People"),
    ("Art.28", "Cybersecurity awareness and basic hygiene", "People"),
    ("Art.29", "Information sharing arrangements", "Cooperation"),
    ("Art.30", "Voluntary notification of significant incidents", "Incidents"),
    ("Art.32", "Supervisory and enforcement measures", "Governance"),
]

PCI_DSS_REQUIREMENTS = [
    ("Req.1", "Install and maintain network security controls", "Network"),
    ("Req.2", "Apply secure configurations to all system components", "Configuration"),
    ("Req.3", "Protect stored account data", "Data protection"),
    ("Req.4", "Protect cardholder data with strong cryptography during transmission", "Data protection"),
    ("Req.5", "Protect all systems and networks from malicious software", "Malware"),
    ("Req.6", "Develop and maintain secure systems and software", "Development"),
    ("Req.7", "Restrict access to system components and cardholder data by business need to know", "Access control"),
    ("Req.8", "Identify users and authenticate access to system components", "Access control"),
    ("Req.9", "Restrict physical access to cardholder data", "Physical"),
    ("Req.10", "Log and monitor all access to system components and cardholder data", "Logging"),
    ("Req.11", "Test security of systems and networks regularly", "Testing"),
    ("Req.12", "Support information security with organizational policies and programs", "Governance"),
]

ISO27005_CLAUSES = [
    ("5.1", "Information security risk management process - establish, implement, maintain, continually improve", "Process"),
    ("5.2", "Alignment with other information security management standards", "Integration"),
    ("5.3", "Critical success factors for information security risk management", "Governance"),
    ("6.2", "Communication and consultation on risk with stakeholders", "Communication"),
    ("6.3.1", "External context of the organization (legal, regulatory, market)", "Context"),
    ("6.3.2", "Internal context of the organization (governance, capabilities, culture)", "Context"),
    ("6.3.3", "Risk criteria - risk appetite, tolerance, impact and likelihood scales", "Context"),
    ("6.4.1", "Risk identification process", "Identification"),
    ("6.4.2", "Identification of assets and their owners", "Identification"),
    ("6.4.3", "Identification of threats and threat sources", "Identification"),
    ("6.4.4", "Identification of vulnerabilities and existing controls", "Identification"),
    ("6.5", "Risk analysis - determine likelihood, impact and level of risk", "Analysis"),
    ("6.6", "Risk evaluation - compare with risk criteria and prioritize", "Evaluation"),
    ("6.7", "Risk treatment - select and document treatment options with controls", "Treatment"),
    ("6.8", "Risk acceptance - formally accept residual risks with sign-off", "Acceptance"),
    ("6.9", "Risk monitoring and review - ongoing and periodic activities", "Monitoring"),
    ("6.10", "Recording and reporting of risk management activities", "Documentation"),
]

ISO22301_CLAUSES = [
    ("4", "Context of the organization", "Context"),
    ("5", "Leadership", "Leadership"),
    ("6", "Planning", "Planning"),
    ("7", "Support", "Support"),
    ("8.2", "Business impact analysis and risk assessment", "Operation"),
    ("8.3", "Business continuity strategies and solutions", "Operation"),
    ("8.4", "Business continuity plans and procedures", "Operation"),
    ("8.5", "Exercise programme", "Operation"),
    ("9", "Performance evaluation", "Evaluation"),
    ("10", "Improvement", "Improvement"),
]


class Command(BaseCommand):
    help = (
        "Seed frameworks for every organization. "
        "Use --frameworks to select: iso27001, nist_csf, soc2, gdpr, nis2, "
        "pci_dss, iso22301, or 'all' (default). "
        "Use --list to see available codes."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--frameworks",
            default="all",
            help="Comma-separated codes to seed, or 'all' (default), or 'none'.",
        )
        parser.add_argument(
            "--list",
            action="store_true",
            help="Only list available framework codes and exit.",
        )

    ALL_CODES = ["iso27001", "iso27005", "nist_csf", "soc2", "gdpr", "nis2", "pci_dss", "iso22301"]

    def handle(self, *args, **opts):
        if opts.get("list"):
            self.stdout.write("Available framework codes:")
            for code in self.ALL_CODES:
                self.stdout.write(f"  - {code}")
            return

        selected = opts["frameworks"]
        if selected == "all":
            codes = list(self.ALL_CODES)
        elif selected == "none" or not selected:
            codes = []
        else:
            codes = [x.strip() for x in selected.split(",") if x.strip()]

        for org in Organization.objects.all():
            for code in codes:
                seed_fn = getattr(self, f"_seed_{code}", None)
                if seed_fn:
                    seed_fn(org)
                else:
                    self.stdout.write(self.style.WARNING(
                        f"[{org.slug}] Unknown framework code: {code}"
                    ))


    # ---- ISO 27001 ----
    def _seed_iso27001(self, org):
        framework, _ = Framework.objects.get_or_create(
            organization=org, code="iso27001",
            defaults={
                "name": "ISO/IEC 27001",
                "category": "Information Security",
                "source_url": "https://www.iso.org/standard/27001",
                "is_system": True,
            },
        )
        version, _ = FrameworkVersion.objects.get_or_create(
            framework=framework, version="2022",
            defaults={"published_at": date(2022, 10, 25), "is_active": True},
        )
        count = 0
        for idx, (code, title, category) in enumerate(ISO27001_CONTROLS):
            _, created = Requirement.objects.get_or_create(
                framework_version=version, code=code,
                defaults={"title": title, "category": category, "order": idx},
            )
            if created:
                count += 1
        self.stdout.write(self.style.SUCCESS(
            f"[{org.slug}] ISO 27001:2022 - {count} new requirements"
        ))

    def _seed_nist_csf(self, org):
        framework, _ = Framework.objects.get_or_create(
            organization=org, code="nist_csf",
            defaults={
                "name": "NIST Cybersecurity Framework",
                "category": "Cybersecurity",
                "source_url": "https://www.nist.gov/cyberframework",
                "is_system": True,
            },
        )
        version, _ = FrameworkVersion.objects.get_or_create(
            framework=framework, version="2.0",
            defaults={"published_at": date(2024, 2, 26), "is_active": True},
        )
        count = 0
        for idx, (code, title, description) in enumerate(NIST_CSF_FUNCTIONS):
            _, created = Requirement.objects.get_or_create(
                framework_version=version, code=code,
                defaults={"title": title, "description": description, "category": "Function", "order": idx},
            )
            if created:
                count += 1
        self.stdout.write(self.style.SUCCESS(
            f"[{org.slug}] NIST CSF 2.0 - {count} new requirements"
        ))


    # ---- New frameworks ----
    def _seed_soc2(self, org):
        self._seed_simple(org, code="soc2", name="SOC 2", category="Security",
                          source_url="https://www.aicpa-cima.com/topic/audit-assurance/audit-and-assurance-greater-than-soc-2",
                          version="2023", requirements=SOC2_CONTROLS)

    def _seed_gdpr(self, org):
        self._seed_simple(org, code="gdpr", name="GDPR", category="Privacy",
                          source_url="https://eur-lex.europa.eu/eli/reg/2016/679/oj",
                          version="2016/679", requirements=GDPR_ARTICLES)

    def _seed_nis2(self, org):
        self._seed_simple(org, code="nis2", name="NIS2 Directive", category="Cybersecurity",
                          source_url="https://eur-lex.europa.eu/eli/dir/2022/2555/oj",
                          version="2022/2555", requirements=NIS2_ARTICLES)

    def _seed_pci_dss(self, org):
        self._seed_simple(org, code="pci_dss", name="PCI DSS", category="Payments",
                          source_url="https://www.pcisecuritystandards.org/",
                          version="4.0", requirements=PCI_DSS_REQUIREMENTS)

    def _seed_iso22301(self, org):
        self._seed_simple(org, code="iso22301", name="ISO 22301", category="Business Continuity",
                          source_url="https://www.iso.org/standard/75106.html",
                          version="2019", requirements=ISO22301_CLAUSES)

    def _seed_iso27005(self, org):
        self._seed_simple(org, code="iso27005", name="ISO/IEC 27005", category="Risk Management",
                          source_url="https://www.iso.org/standard/80585.html",
                          version="2022", requirements=ISO27005_CLAUSES)

    def _seed_simple(self, org, code, name, category, source_url, version, requirements):
        framework, _ = Framework.objects.get_or_create(
            organization=org, code=code,
            defaults={"name": name, "category": category,
                      "source_url": source_url, "is_system": True},
        )
        fv, _ = FrameworkVersion.objects.get_or_create(
            framework=framework, version=version,
            defaults={"published_at": date(2023, 1, 1), "is_active": True},
        )
        count = 0
        for idx, (rcode, rtitle, rcat) in enumerate(requirements):
            _, created = Requirement.objects.get_or_create(
                framework_version=fv, code=rcode,
                defaults={"title": rtitle, "category": rcat, "order": idx},
            )
            if created:
                count += 1
        self.stdout.write(self.style.SUCCESS(
            f"[{org.slug}] {name} {version} - {count} new requirements"
        ))