"""Tool definitions and executors for the LocalGRC assistant.

The assistant can call these read-only tools to query platform data.
All queries are scoped to the requesting user's organization.
"""

import json

from django.utils import timezone


TOOL_DEFINITIONS = [
    {"type": "function", "function": {
        "name": "list_risks",
        "description": "List risks in the organization. Optionally filter by severity or status.",
        "parameters": {"type": "object", "properties": {
            "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
            "status": {"type": "string", "enum": ["draft", "under_review", "approved", "mitigating", "closed"]},
            "limit": {"type": "integer", "default": 10},
        }, "required": []},
    }},
    {"type": "function", "function": {
        "name": "get_risk",
        "description": "Get full details of a specific risk by its code (e.g. R-0001).",
        "parameters": {"type": "object", "properties": {
            "code": {"type": "string"},
        }, "required": ["code"]},
    }},
    {"type": "function", "function": {
        "name": "list_controls",
        "description": "List controls in the organization.",
        "parameters": {"type": "object", "properties": {
            "status": {"type": "string", "enum": ["draft", "approved", "implemented", "retired"]},
            "limit": {"type": "integer", "default": 10},
        }, "required": []},
    }},
    {"type": "function", "function": {
        "name": "framework_coverage",
        "description": "Return compliance coverage percentage for a framework (iso27001, nist_csf, gdpr).",
        "parameters": {"type": "object", "properties": {
            "framework_code": {"type": "string"},
        }, "required": ["framework_code"]},
    }},
    {"type": "function", "function": {
        "name": "list_open_findings",
        "description": "List open audit findings (non-conformities, observations).",
        "parameters": {"type": "object", "properties": {
            "severity": {"type": "string", "enum": ["major_nc", "minor_nc", "observation", "opportunity"]},
            "limit": {"type": "integer", "default": 10},
        }, "required": []},
    }},
    {"type": "function", "function": {
        "name": "list_overdue_deadlines",
        "description": "List regulatory deadlines that are overdue (not yet notified past deadline).",
        "parameters": {"type": "object", "properties": {}, "required": []},
    }},
    {"type": "function", "function": {
        "name": "list_incidents",
        "description": "List incidents in the organization.",
        "parameters": {"type": "object", "properties": {
            "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
            "status": {"type": "string", "enum": ["detected", "triaged", "contained", "eradicated", "recovered", "closed"]},
            "limit": {"type": "integer", "default": 10},
        }, "required": []},
    }},
    {"type": "function", "function": {
        "name": "list_critical_vendors_without_dpa",
        "description": "List high/critical vendors that have not signed a Data Processing Agreement.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    }},
    {"type": "function", "function": {
        "name": "list_expired_evidence",
        "description": "List evidence items whose validity period has expired.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    }},
    {"type": "function", "function": {
        "name": "list_vulnerabilities",
        "description": "List vulnerabilities in the organization.",
        "parameters": {"type": "object", "properties": {
            "severity": {"type": "string", "enum": ["critical", "high", "medium", "low", "info"]},
            "status": {"type": "string", "enum": ["open", "in_progress", "mitigated", "accepted", "false_positive"]},
            "limit": {"type": "integer", "default": 10},
        }, "required": []},
    }},
    {"type": "function", "function": {
        "name": "dashboard_summary",
        "description": "Get a high-level GRC posture summary: risk counts by level, open findings, open incidents, overdue deadlines, expired evidence, critical vendors without DPA, vulnerabilities by severity.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    }},
]


class ToolExecutor:
    """Executes tool calls scoped to an organization + user."""

    def __init__(self, organization, user):
        self.org = organization
        self.user = user

    def execute(self, name, arguments):
        method = getattr(self, name, None)
        if method is None or not callable(method):
            return json.dumps({"error": f"Unknown tool: {name}"})
        try:
            return json.dumps(method(**(arguments or {})), default=str)
        except TypeError as e:
            return json.dumps({"error": f"Invalid args for {name}: {e}"})
        except Exception as e:
            return json.dumps({"error": f"Tool {name} failed: {e}"})

    def list_risks(self, severity=None, status=None, limit=10):
        from apps.risks.models import Risk
        qs = Risk.objects.filter(organization=self.org).select_related("owner")
        if status:
            qs = qs.filter(status=status)
        risks = list(qs[:200])
        if severity:
            risks = [r for r in risks if r.risk_level == severity]
        risks = risks[:limit]
        return {"count": len(risks), "risks": [
            {"code": r.code, "title": r.title, "category": r.get_category_display(),
             "status": r.get_status_display(), "level": r.risk_level,
             "residual_score": r.residual_score, "inherent_score": r.inherent_score,
             "owner": r.owner.full_name if r.owner else None}
            for r in risks]}

    def get_risk(self, code):
        from apps.risks.models import Risk
        try:
            r = Risk.objects.get(organization=self.org, code=code)
        except Risk.DoesNotExist:
            return {"error": f"Risk {code} not found"}
        return {
            "code": r.code, "title": r.title, "description": r.description,
            "category": r.get_category_display(), "status": r.get_status_display(),
            "level": r.risk_level, "owner": r.owner.full_name if r.owner else None,
            "assessments": [{"type": a.get_type_display(), "likelihood": a.likelihood,
                             "impact": a.impact, "score": a.score, "is_current": a.is_current}
                            for a in r.assessments.all()],
            "treatments": [{"strategy": t.get_strategy_display(), "description": t.description,
                            "status": t.get_status_display(), "due_date": t.due_date}
                           for t in r.treatments.all()],
        }

    def list_controls(self, status=None, limit=10):
        from apps.controls.models import Control
        qs = Control.objects.filter(organization=self.org)
        if status:
            qs = qs.filter(status=status)
        controls = qs[:limit]
        return {"count": len(controls), "controls": [
            {"code": c.code, "name": c.name, "type": c.get_control_type_display(),
             "status": c.get_status_display(), "category": c.category,
             "requirements_count": c.requirement_links.count()}
            for c in controls]}

    def framework_coverage(self, framework_code):
        from apps.frameworks.models import Framework
        from apps.controls.models import ControlRequirement
        fw = Framework.objects.filter(organization=self.org, code=framework_code).first()
        if not fw:
            return {"error": f"Framework {framework_code} not found"}
        version = fw.versions.filter(is_active=True).first() or fw.versions.first()
        if not version:
            return {"error": "No version"}
        reqs = version.requirements.all()
        total = reqs.count()
        covered = ControlRequirement.objects.filter(requirement__in=reqs, coverage="full").values("requirement").distinct().count()
        partial = ControlRequirement.objects.filter(requirement__in=reqs, coverage="partial").values("requirement").distinct().count()
        return {"framework": fw.name, "version": version.version,
                "total_requirements": total, "fully_covered": covered,
                "partially_covered": partial,
                "coverage_pct": round((covered / total) * 100) if total else 0}

    def list_open_findings(self, severity=None, limit=10):
        from apps.audits.models import AuditFinding
        qs = AuditFinding.objects.filter(audit__organization=self.org).exclude(status__in=["verified", "closed"])
        if severity:
            qs = qs.filter(severity=severity)
        findings = qs[:limit]
        return {"count": len(findings), "findings": [
            {"code": f.code, "title": f.title, "severity": f.get_severity_display(),
             "status": f.get_status_display(), "audit": f.audit.title}
            for f in findings]}

    def list_overdue_deadlines(self):
        from apps.incidents.models import RegulatoryDeadline
        now = timezone.now()
        qs = RegulatoryDeadline.objects.filter(
            incident__organization=self.org, notified_at__isnull=True
        ).select_related("incident")
        overdue = [d for d in qs if d.deadline_at < now]
        return {"count": len(overdue), "deadlines": [
            {"incident": d.incident.code, "incident_title": d.incident.title,
             "regulation": d.get_regulation_display(), "deadline": d.deadline_at,
             "overdue_by_hours": round((now - d.deadline_at).total_seconds() / 3600, 1)}
            for d in overdue]}

    def list_incidents(self, severity=None, status=None, limit=10):
        from apps.incidents.models import Incident
        qs = Incident.objects.filter(organization=self.org)
        if severity:
            qs = qs.filter(severity=severity)
        if status:
            qs = qs.filter(status=status)
        incidents = qs[:limit]
        return {"count": len(incidents), "incidents": [
            {"code": i.code, "title": i.title, "category": i.get_category_display(),
             "severity": i.get_severity_display(), "status": i.get_status_display(),
             "detected_at": i.detected_at}
            for i in incidents]}

    def list_critical_vendors_without_dpa(self):
        from apps.vendors.models import Vendor
        vendors = Vendor.objects.filter(organization=self.org, criticality__in=["high", "critical"], dpa_signed=False)
        return {"count": vendors.count(), "vendors": [
            {"name": v.name, "criticality": v.get_criticality_display(),
             "data_role": v.get_data_processing_role_display()}
            for v in vendors]}

    def list_expired_evidence(self):
        from apps.evidence.models import Evidence
        today = timezone.now().date()
        qs = Evidence.objects.filter(organization=self.org, valid_until__lt=today)
        return {"count": qs.count(), "items": [
            {"title": e.title, "linked_to": e.target_display,
             "valid_until": e.valid_until, "days_overdue": (today - e.valid_until).days}
            for e in qs[:20]]}

    def list_vulnerabilities(self, severity=None, status=None, limit=10):
        from apps.vulnerabilities.models import Vulnerability
        qs = Vulnerability.objects.filter(organization=self.org)
        if severity:
            qs = qs.filter(severity=severity)
        if status:
            qs = qs.filter(status=status)
        vulns = qs[:limit]
        return {"count": len(vulns), "vulnerabilities": [
            {"title": v.title, "cve_id": v.cve_id, "severity": v.get_severity_display(),
             "status": v.get_status_display(), "affected_endpoint": v.affected_endpoint,
             "cvss_score": float(v.cvss_score) if v.cvss_score else None}
            for v in vulns]}

    def dashboard_summary(self):
        from apps.risks.models import Risk
        from apps.audits.models import AuditFinding
        from apps.incidents.models import Incident, RegulatoryDeadline
        from apps.evidence.models import Evidence
        from apps.vendors.models import Vendor
        from apps.vulnerabilities.models import Vulnerability

        risks = list(Risk.objects.filter(organization=self.org))
        by_level = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for r in risks:
            if r.risk_level in by_level:
                by_level[r.risk_level] += 1

        now = timezone.now()
        overdue = sum(1 for d in RegulatoryDeadline.objects.filter(
            incident__organization=self.org, notified_at__isnull=True) if d.deadline_at < now)

        today = timezone.now().date()
        vuln_by_sev = {}
        for v in Vulnerability.objects.filter(organization=self.org).exclude(
                status__in=["mitigated", "accepted", "false_positive"]):
            vuln_by_sev[v.severity] = vuln_by_sev.get(v.severity, 0) + 1

        return {
            "risks": {"total": len(risks), "by_level": by_level},
            "open_findings": AuditFinding.objects.filter(audit__organization=self.org).exclude(status__in=["verified", "closed"]).count(),
            "open_incidents": Incident.objects.filter(organization=self.org).exclude(status="closed").count(),
            "overdue_deadlines": overdue,
            "expired_evidence": Evidence.objects.filter(organization=self.org, valid_until__lt=today).count(),
            "critical_vendors_without_dpa": Vendor.objects.filter(organization=self.org, criticality__in=["high", "critical"], dpa_signed=False).count(),
            "open_vulnerabilities_by_severity": vuln_by_sev,
        }