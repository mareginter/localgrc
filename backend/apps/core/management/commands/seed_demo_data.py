"""seed_demo_data — populate LocalGRC with realistic demo data.

Usage:
  docker compose exec app python manage.py seed_demo_data
  docker compose exec app python manage.py seed_demo_data --clean --yes

Idempotent: uses get_or_create on natural keys (org + name/title), so
running twice does not duplicate. `--clean` wipes all business data
first (keeps users, orgs, frameworks, requirements, workflow definitions).
"""

from datetime import date, timedelta

from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.audits.models import Audit, AuditFinding, CorrectiveAction
from apps.controls.models import Control, ControlImplementation, ControlRequirement
from apps.core.models import Organization, User, WorkflowDefinition, WorkflowInstance
from apps.evidence.models import Evidence
from apps.frameworks.models import FrameworkVersion, Requirement
from apps.incidents.models import Incident, RegulatoryDeadline, ensure_regulatory_deadlines
from apps.policies.models import Policy, PolicyApproval, PolicyVersion
from apps.risks.models import (
    Asset, Risk, RiskAssessment, RiskAsset, RiskControl, RiskTreatment,
)
from apps.vendors.models import Vendor, VendorAssessment, VendorControl, VendorRisk


ASSETS = [
    ("Customer CRM database", "data", "critical", "restricted", "Customer PII in PostgreSQL"),
    ("Payment gateway", "system", "critical", "restricted", "Stripe integration"),
    ("HR system (BambooHR)", "system", "high", "confidential", "Employee records"),
    ("Main office (Lisbon)", "facility", "high", "internal", "HQ + server room"),
    ("Datacenter rack A", "facility", "critical", "internal", "Primary colocation"),
    ("Engineering team", "people", "medium", "internal", "Product + platform"),
    ("AWS production account", "system", "critical", "restricted", "Prod workloads"),
    ("Zendesk ticketing", "service", "high", "confidential", "Support tickets with PII"),
    ("Source code (GitHub)", "system", "critical", "restricted", "Org repos"),
    ("Backup storage (S3)", "data", "critical", "restricted", "Encrypted backups"),
]

EXTRA_CONTROLS = [
    ("Security awareness training", "preventive", "People", ["A.6.3"], "Annual phishing simulation + training."),
    ("Vulnerability management", "detective", "Technical", ["A.8.8"], "Weekly scans + patch SLA 30d."),
    ("Change management process", "preventive", "Technical", ["A.8.32"], "CAB approval + rollback plan."),
    ("Supplier due diligence", "preventive", "Organizational", ["A.5.19", "A.5.20"], "Pre-contract assessment + DPA."),
    ("Business continuity plan", "corrective", "Organizational", ["A.5.29", "A.5.30"], "RTO 4h, RPO 1h, tested annually."),
    ("Endpoint protection (EDR)", "preventive", "Technical", ["A.8.1"], "CrowdStrike on all endpoints."),
    ("Secure SDLC", "preventive", "Technical", ["A.8.25", "A.8.28"], "SAST/DAST in CI + code review."),
    ("Data classification", "preventive", "Organizational", ["A.5.12", "A.5.13"], "4 levels: public/internal/confidential/restricted."),
    ("Incident response procedure", "corrective", "Organizational", ["A.5.24", "A.5.26"], "24/7 on-call + playbooks."),
    ("Cryptography standard", "preventive", "Technical", ["A.8.24"], "AES-256 at rest, TLS 1.2+ in transit."),
]

RISKS = [
    ("Phishing targeting finance team", "security", 4, 5, 2, 4, "mitigate", ["Customer CRM database", "Main office (Lisbon)"], ["Multi-factor authentication", "Security awareness training"]),
    ("Data breach via third-party vendor", "privacy", 3, 5, 2, 5, "mitigate", ["Customer CRM database"], ["Supplier due diligence"]),
    ("Unpatched systems expose CVEs", "security", 4, 4, 2, 3, "mitigate", ["AWS production account", "Source code (GitHub)"], ["Vulnerability management", "Endpoint protection (EDR)"]),
    ("Insider data exfiltration", "security", 2, 5, 2, 4, "mitigate", ["Customer CRM database", "Engineering team"], ["Access control policy", "Data classification"]),
    ("Ransomware on file servers", "operational", 3, 5, 2, 4, "mitigate", ["Backup storage (S3)", "Datacenter rack A"], ["Backup and restore", "Endpoint protection (EDR)"]),
    ("Loss of key engineer (bus factor)", "strategic", 3, 3, 2, 3, "accept", ["Engineering team"], []),
    ("Cloud provider outage", "operational", 2, 4, 2, 3, "transfer", ["AWS production account"], ["Business continuity plan"]),
    ("GDPR fine from a data breach", "compliance", 2, 5, 1, 4, "mitigate", ["Customer CRM database", "Zendesk ticketing"], ["Data classification", "Incident response procedure"]),
    ("Fraud in expense reports", "financial", 3, 2, 3, 2, "accept", [], []),
    ("Social engineering of helpdesk", "security", 3, 4, 2, 3, "mitigate", ["Engineering team", "Main office (Lisbon)"], ["Security awareness training"]),
    ("S3 bucket misconfig exposing backups", "security", 2, 5, 1, 5, "mitigate", ["Backup storage (S3)"], ["Cryptography standard"]),
    ("Unencrypted laptops in transit", "operational", 3, 4, 1, 4, "mitigate", ["Engineering team"], ["Endpoint protection (EDR)", "Cryptography standard"]),
    ("Supply chain attack via npm", "security", 3, 5, 2, 4, "mitigate", ["Source code (GitHub)"], ["Secure SDLC", "Vulnerability management"]),
    ("Misconfigured change deployment", "operational", 3, 3, 2, 2, "mitigate", ["AWS production account", "Source code (GitHub)"], ["Change management process", "Secure SDLC"]),
]

POLICIES = [
    ("Acceptable Use Policy", "security", "published", "Rules for acceptable use of company systems."),
    ("Access Control Policy", "security", "published", "Least privilege, MFA, quarterly reviews."),
    ("Information Classification Policy", "governance", "published", "4 classification levels + handling."),
    ("Incident Response Plan", "security", "in_review", "Detection, response, notification."),
    ("Business Continuity Plan", "operational", "approved", "RTO 4h, RPO 1h."),
    ("Vendor Management Policy", "governance", "published", "Due diligence, DPA, annual reviews."),
    ("Remote Work Policy", "hr", "published", "Remote access, BYOD rules."),
    ("Data Retention Policy", "privacy", "draft", "Retention per data category."),
]

VENDORS = [
    ("Amazon Web Services", "Cloud", "critical", "processor", True),
    ("Stripe", "Payments", "critical", "processor", True),
    ("BambooHR", "HR SaaS", "high", "processor", True),
    ("Zendesk", "Support SaaS", "high", "processor", True),
    ("Google Workspace", "Productivity", "high", "processor", True),
    ("Cloudflare", "CDN/WAF", "critical", "processor", True),
    ("Slack", "Communications", "medium", "processor", True),
    ("Datadog", "Observability", "medium", "processor", False),
    ("GitHub", "Code hosting", "critical", "processor", True),
    ("Twilio", "SMS/voice", "medium", "processor", False),
]

INCIDENTS = [
    ("Phishing campaign on finance team", "security", "high", 6, "triaged"),
    ("Suspicious login on admin portal", "security", "medium", 72, "contained"),
    ("S3 bucket misconfiguration detected", "data_breach", "critical", 4, "detected"),
    ("Zendesk outage affecting tickets", "service_disruption", "medium", 120, "recovered"),
]

AUDITS = [
    ("ISO 27001 internal audit 2026", "internal", "in_progress", -7, 7),
    ("PCI DSS surveillance audit", "external", "planned", 30, 35),
    ("AWS supplier audit", "supplier", "completed", -90, -85),
]

FINDINGS = [
    ("ISO 27001 internal audit 2026", "minor_nc", "Access reviews not performed Q3", "A.5.18", "in_progress"),
    ("ISO 27001 internal audit 2026", "observation", "Backup restore not tested since 2025", "A.8.13", "open"),
    ("ISO 27001 internal audit 2026", "major_nc", "No documented change management process", "A.8.32", "open"),
    ("PCI DSS surveillance audit", "minor_nc", "Firewall rules not reviewed quarterly", "A.8.20", "open"),
    ("AWS supplier audit", "observation", "MFA not enforced for support tier", "A.5.17", "resolved"),
]


class Command(BaseCommand):
    help = "Populate LocalGRC with realistic demo data (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--clean", action="store_true",
                            help="Delete all business data first (destructive!)")
        parser.add_argument("--yes", action="store_true",
                            help="Skip confirmation prompt for --clean")

    def handle(self, *args, **opts):
        org = Organization.objects.first()
        if not org:
            self.stderr.write(self.style.ERROR(
                "No organization. Run `bootstrap` first."))
            return

        self.stdout.write("Ensuring workflows and frameworks are seeded...")
        for cmd in ["seed_frameworks", "seed_risk_workflow", "seed_control_workflow",
                    "seed_policy_workflow", "seed_vendor_workflow",
                    "seed_incident_workflow", "seed_audit_workflows",
                    "seed_sample_controls"]:
            try:
                call_command(cmd, verbosity=0)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  {cmd}: {e}"))

        if opts["clean"]:
            if not opts["yes"]:
                ans = input("Type YES to wipe ALL business data: ")
                if ans != "YES":
                    self.stdout.write("Aborted.")
                    return
            self._wipe()

        admin = User.objects.filter(is_superuser=True).first()
        today = date.today()

        assets = self._assets(org)
        self.stdout.write(f"  Assets: {len(assets)}")

        controls = self._controls(org, admin)
        self.stdout.write(f"  Controls: {len(controls)}")

        risks = self._risks(org, admin, assets, controls, today)
        self.stdout.write(f"  Risks: {len(risks)}")

        policies = self._policies(org, admin, today)
        self.stdout.write(f"  Policies: {len(policies)}")

        vendors = self._vendors(org, admin, risks, today)
        self.stdout.write(f"  Vendors: {len(vendors)}")

        incidents = self._incidents(org, admin, risks, vendors, today)
        self.stdout.write(f"  Incidents: {len(incidents)}")

        audits = self._audits(org, admin, today)
        self.stdout.write(f"  Audits: {len(audits)}")

        ev = self._evidence(org, admin, controls, today)
        self.stdout.write(f"  Evidence: {len(ev)}")

        self.stdout.write(self.style.SUCCESS(
            "\nDone. Visit / to see the dashboard."))

    # ------------------------------------------------------------------ wipe
    def _wipe(self):
        from apps.core.models import Attachment, Comment, Notification, Tag, TaggedItem
        self.stdout.write(self.style.WARNING("Wiping business data..."))
        order = [
            Evidence, RegulatoryDeadline, CorrectiveAction, AuditFinding, Audit,
            PolicyApproval, PolicyVersion, Policy,
            VendorControl, VendorRisk, VendorAssessment, Vendor,
            RiskControl, RiskTreatment, RiskAssessment, RiskAsset, Risk,
            ControlImplementation, ControlRequirement, Control, Asset,
            Comment, Attachment, TaggedItem, Tag, Notification, WorkflowInstance,
        ]
        for m in order:
            try:
                n = m.objects.count()
                if n:
                    m.objects.all().delete()
                    self.stdout.write(f"  {m.__name__}: {n}")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  {m.__name__}: {e}"))

    # ------------------------------------------------------ workflow helper
    def _wf(self, obj, model, status):
        ct = ContentType.objects.get_for_model(model)
        defn = WorkflowDefinition.objects.filter(
            organization_id=obj.organization_id,
            content_type=ct, is_default=True).first()
        if not defn:
            return
        state = defn.states.filter(code=status).first()
        if not state:
            state = defn.states.order_by("order").first()
        if not state:
            return
        WorkflowInstance.objects.get_or_create(
            content_type=ct, object_id=obj.pk,
            defaults={"definition": defn, "current_state": state},
        )

    # -------------------------------------------------------------- assets
    def _assets(self, org):
        out = []
        for name, typ, crit, cls, desc in ASSETS:
            a, _ = Asset.objects.get_or_create(
                organization=org, name=name,
                defaults={"type": typ, "criticality": crit,
                          "classification": cls, "description": desc})
            out.append(a)
        return out

    # ------------------------------------------------------------ controls
    def _controls(self, org, admin):
        iso = FrameworkVersion.objects.filter(
            framework__organization=org, framework__code="iso27001",
            is_active=True).first()
        out = []
        # existing sample controls from seed_sample_controls + new extras
        names = [c[0] for c in EXTRA_CONTROLS]
        all_controls = list(Control.objects.filter(organization=org))
        for name, ctype, cat, reqs, desc in EXTRA_CONTROLS:
            c, _ = Control.objects.get_or_create(
                organization=org, name=name,
                defaults={"control_type": ctype, "category": cat,
                          "description": desc, "owner": admin,
                          "status": "approved"})
            if iso:
                for rcode in reqs:
                    req = Requirement.objects.filter(
                        framework_version=iso, code=rcode).first()
                    if req:
                        ControlRequirement.objects.get_or_create(
                            control=c, requirement=req,
                            defaults={"coverage": "full"})
            out.append(c)
        # return ALL controls (sample + extras) so risks can link to any
        return list(Control.objects.filter(organization=org))

    # --------------------------------------------------------------- risks
    def _risks(self, org, admin, assets, controls, today):
        asset_map = {a.name: a for a in assets}
        control_map = {c.name: c for c in controls}
        out = []
        for (title, cat, li, ii, rl, ri, strat, asset_names, ctrl_names) in RISKS:
            risk, _ = Risk.objects.get_or_create(
                organization=org, title=title,
                defaults={"category": cat, "status": "approved",
                          "owner": admin, "description": f"Demo: {title}"})
            # assessments
            RiskAssessment.objects.get_or_create(
                risk=risk, type="inherent",
                defaults={"likelihood": li, "impact": ii,
                          "is_current": True, "assessed_by": admin})
            RiskAssessment.objects.get_or_create(
                risk=risk, type="residual",
                defaults={"likelihood": rl, "impact": ri,
                          "is_current": True, "assessed_by": admin})
            # treatment
            RiskTreatment.objects.get_or_create(
                risk=risk, strategy=strat,
                defaults={"description": f"Treatment plan for {title}",
                          "responsible": admin, "status": "in_progress",
                          "due_date": today + timedelta(days=90)})
            # link assets
            for an in asset_names:
                a = asset_map.get(an)
                if a:
                    RiskAsset.objects.get_or_create(risk=risk, asset=a)
            # link controls
            for cn in ctrl_names:
                c = control_map.get(cn)
                if c:
                    RiskControl.objects.get_or_create(
                        risk=risk, control=c,
                        defaults={"effectiveness": "medium"})
            self._wf(risk, Risk, risk.status)
            out.append(risk)
        return out

    # ------------------------------------------------------------ policies
    def _policies(self, org, admin, today):
        out = []
        for title, cat, status, summary in POLICIES:
            p, _ = Policy.objects.get_or_create(
                organization=org, title=title,
                defaults={"category": cat, "status": status,
                          "owner": admin, "summary": summary})
            # version 1
            v, _ = PolicyVersion.objects.get_or_create(
                policy=p, version_number=1,
                defaults={"content": f"# {title}\n\n{summary}\n\nFull text pending.",
                          "effective_date": today - timedelta(days=90),
                          "next_review_date": today + timedelta(days=275),
                          "change_summary": "Initial version"})
            # if published/approved, mark version approved
            if status in ("published", "approved") and not v.approved_at:
                v.approved_by = admin
                v.approved_at = timezone.now() - timedelta(days=85)
                v.save(update_fields=["approved_by", "approved_at", "updated_at"])
                p.current_version = v
                p.save(update_fields=["current_version", "updated_at"])
                PolicyApproval.objects.get_or_create(
                    policy_version=v, approver=admin,
                    defaults={"decision": "approved",
                              "comment": "Approved during demo seed"})
            self._wf(p, Policy, p.status)
            out.append(p)
        return out

    # ------------------------------------------------------------- vendors
    def _vendors(self, org, admin, risks, today):
        out = []
        for name, cat, crit, role, dpa in VENDORS:
            v, _ = Vendor.objects.get_or_create(
                organization=org, name=name,
                defaults={"category": cat, "criticality": crit,
                          "data_processing_role": role,
                          "dpa_signed": dpa,
                          "dpa_date": today - timedelta(days=180) if dpa else None,
                          "contact_email": f"security@{name.lower().replace(' ', '')}.example",
                          "status": "active"})
            # assessment (varied scores)
            import random
            rng = random.Random(hash(name))
            score = rng.randint(55, 95)
            rating = "low" if score >= 80 else ("medium" if score >= 65 else "high")
            VendorAssessment.objects.get_or_create(
                vendor=v, assessment_date=today - timedelta(days=60),
                defaults={"score": score, "risk_rating": rating,
                          "next_assessment_date": today + timedelta(days=305),
                          "assessed_by": admin,
                          "findings_summary": f"Score {score}/100. No critical findings."})
            self._wf(v, Vendor, v.status)
            out.append(v)
        # link a couple of vendors to risks
        aws = next((v for v in out if "AWS" in v.name), None)
        if aws and risks:
            VendorRisk.objects.get_or_create(
                vendor=aws, risk=risks[6],  # Cloud outage
                defaults={"note": "Single-region risk"})
        return out

    # ----------------------------------------------------------- incidents
    def _incidents(self, org, admin, risks, vendors, today):
        out = []
        for title, cat, sev, hours_ago, status in INCIDENTS:
            inc, _ = Incident.objects.get_or_create(
                organization=org, title=title,
                defaults={"category": cat, "severity": sev, "status": status,
                          "detected_at": timezone.now() - timedelta(hours=hours_ago),
                          "reported_by": admin, "owner": admin,
                          "description": f"Demo: {title}"})
            ensure_regulatory_deadlines(inc)
            self._wf(inc, Incident, inc.status)
            out.append(inc)
        return out

    # -------------------------------------------------------------- audits
    def _audits(self, org, admin, today):
        audit_map = {}
        for title, atyp, status, start_off, end_off in AUDITS:
            a, _ = Audit.objects.get_or_create(
                organization=org, title=title,
                defaults={"audit_type": atyp, "status": status,
                          "lead_auditor": admin,
                          "auditor_org": "BSI" if atyp == "certification" else "",
                          "planned_start": today + timedelta(days=start_off),
                          "planned_end": today + timedelta(days=end_off),
                          "scope": f"Scope for {title}"})
            self._wf(a, Audit, a.status)
            audit_map[title] = a

        # ISO version for requirement links
        iso = FrameworkVersion.objects.filter(
            framework__organization=org, framework__code="iso27001").first()

        for audit_title, sev, f_title, req_code, f_status in FINDINGS:
            audit = audit_map.get(audit_title)
            if not audit:
                continue
            req = Requirement.objects.filter(
                framework_version=iso, code=req_code).first() if iso else None
            f, _ = AuditFinding.objects.get_or_create(
                audit=audit, title=f_title,
                defaults={"severity": sev, "status": f_status,
                          "requirement": req,
                          "description": f"Finding from {audit_title}"})
            # corrective action for non-observation findings
            if sev in ("minor_nc", "major_nc"):
                CorrectiveAction.objects.get_or_create(
                    finding=f, description=f"Remediate: {f_title}",
                    defaults={"responsible": admin, "status": "in_progress",
                              "due_date": today + timedelta(days=60)})
        return list(audit_map.values())

    # ------------------------------------------------------------ evidence
    def _evidence(self, org, admin, controls, today):
        # link evidence to controls by name
        ctrl_map = {c.name: c for c in controls}
        targets = [
            ("Multi-factor authentication", "MFA configuration screenshot",
             "screenshot", -30, 180, True),
            ("Logging and monitoring", "Q3 log retention export",
             "log_export", -90, 90, True),
            ("Backup and restore", "Q2 backup restore test report",
             "manual", -60, 30, True),
            ("Security awareness training", "Phishing simulation results Q3",
             "manual", -30, 335, False),
            ("Access control policy", "Q3 access review spreadsheet",
             "manual", -45, -5, True),   # expired on purpose
            ("Vulnerability management", "October scan report",
             "scan", -15, 15, True),
            ("Data classification", "Data classification rollout memo",
             "manual", -120, 245, True),
            ("Endpoint protection (EDR)", "EDR coverage report",
             "manual", -10, 20, True),
        ]
        out = []
        for ctrl_name, title, source, valid_off, valid_end, verified in targets:
            ctrl = ctrl_map.get(ctrl_name)
            if not ctrl:
                continue
            ct = ContentType.objects.get_for_model(Control)
            valid_from = today + timedelta(days=valid_off)
            valid_until = today + timedelta(days=valid_end)
            e, _ = Evidence.objects.get_or_create(
                organization=org, title=title,
                defaults={"content_type": ct, "object_id": ctrl.pk,
                          "source": source,
                          "description": f"Demo evidence: {title}",
                          "valid_from": valid_from,
                          "valid_until": valid_until,
                          "collected_by": admin,
                          "verified_by": admin if verified else None,
                          "verified_at": timezone.now() - timedelta(days=abs(valid_off) - 5) if verified else None})
            out.append(e)
        return out