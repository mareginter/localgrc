from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from apps.library.models import DocumentTemplate

class Command(BaseCommand):
    help = "Seeds the document library with sample GRC templates."

    def handle(self, *args, **kwargs):
        User = get_user_model()
        admin_user = User.objects.filter(is_superuser=True).first()

        self.stdout.write("A verificar e criar templates de exemplo...")

        templates = [
            # --- POLICIES ---
            {
                "title": "Information Security Policy Template",
                "description": "Standard template for drafting the organization's top-level security policy.",
                "category": "policy",
                "filename": "security_policy_template.txt",
                "content": "INFORMATION SECURITY POLICY\n\n1. Purpose\nThis policy establishes the rules for protecting information assets...\n\n2. Scope\nApplies to all employees, contractors, and third parties...\n\n3. Policy Statements\n- Passwords must be at least 14 characters.\n- MFA is required for all remote access.\n- Data must be classified and encrypted at rest."
            },
            {
                "title": "Access Control Policy",
                "description": "Rules for granting, reviewing, and revoking user access.",
                "category": "policy",
                "filename": "access_control_policy.txt",
                "content": "ACCESS CONTROL POLICY\n\n1. Principle of Least Privilege\nUsers shall only be granted the minimum access necessary to perform their job functions.\n\n2. Access Reviews\nAll privileged accounts must be reviewed quarterly.\n\n3. Offboarding\nAll access must be revoked within 4 hours of an employee's termination."
            },
            {
                "title": "Data Classification Policy",
                "description": "How to label and handle data based on its sensitivity.",
                "category": "policy",
                "filename": "data_classification_policy.txt",
                "content": "DATA CLASSIFICATION POLICY\n\nLevels:\n- PUBLIC: Safe for public release.\n- INTERNAL: Only for employees.\n- CONFIDENTIAL: Need-to-know basis (e.g., PII, financials).\n- RESTRICTED: Highly sensitive (e.g., trade secrets).\n\nHandling: CONFIDENTIAL and RESTRICTED data must be encrypted at rest and in transit."
            },
            {
                "title": "Business Continuity Plan (BCP) Outline",
                "description": "Framework for maintaining operations during a disaster.",
                "category": "policy",
                "filename": "bcp_outline.txt",
                "content": "BUSINESS CONTINUITY PLAN\n\n1. Business Impact Analysis (BIA)\nIdentify critical business functions and their RTO/RPO.\n\n2. Recovery Strategies\n- Alternate sites\n- Cloud failover\n- Manual workarounds\n\n3. Testing\nAnnual tabletop exercises and technical DR tests."
            },
            
            # --- RISKS ---
            {
                "title": "Risk Assessment Form",
                "description": "Spreadsheet template for identifying and scoring risks.",
                "category": "risk",
                "filename": "risk_assessment_form.csv",
                "content": "Risk ID,Asset,Threat,Vulnerability,Likelihood,Impact,Score,Treatment\nR-001,Database,SQL Injection,Unpatched web app,4,5,20,Mitigate\nR-002,Office,Fire,No suppression system,2,5,10,Transfer\nR-003,Cloud,S3 Bucket Leak,Public misconfiguration,3,5,15,Mitigate"
            },
            {
                "title": "Risk Treatment Plan Template",
                "description": "Document to track remediation actions for identified risks.",
                "category": "risk",
                "filename": "risk_treatment_plan.csv",
                "content": "Risk ID,Treatment Strategy,Action Item,Owner,Due Date,Status\nR-001,Mitigate,Implement WAF and patch server,IT Team,2026-12-31,In Progress\nR-003,Mitigate,Enable AWS Block Public Access,Cloud Team,2026-11-30,Completed"
            },

            # --- AUDITS ---
            {
                "title": "ISO 27001 Internal Audit Checklist",
                "description": "Basic checklist to evaluate compliance with ISO 27001 clauses.",
                "category": "audit",
                "filename": "iso27001_audit_checklist.csv",
                "content": "Clause,Requirement,Compliant?,Evidence,Notes\n4,Context of the organization,Yes,Org Chart and SWOT,OK\n5,Leadership,Yes,Minutes of Management Review,OK\n6,Planning,No,Missing Risk Treatment Plan,Needs action\n7,Support,Yes,Training records,OK\n8,Operation,Partial,Incident log exists but not tested,N/A"
            },

            # --- INCIDENTS ---
            {
                "title": "Incident Response Plan Outline",
                "description": "Checklist for managing a cybersecurity incident.",
                "category": "incident",
                "filename": "incident_response_outline.txt",
                "content": "INCIDENT RESPONSE PLAN\n\nPhase 1: Preparation\nPhase 2: Detection and Analysis\nPhase 3: Containment, Eradication, and Recovery\nPhase 4: Post-Incident Activity\n\nGDPR Note: The DPO must be notified within 72 hours if a data breach occurs."
            },
            {
                "title": "GDPR Data Breach Notification Form",
                "description": "Form to document a data breach for the supervisory authority.",
                "category": "incident",
                "filename": "gdpr_breach_form.txt",
                "content": "GDPR BREACH NOTIFICATION FORM\n\n1. Nature of the breach: [Describe]\n2. Categories and number of data subjects concerned: [Number]\n3. Categories and number of personal data records concerned: [Number]\n4. Contact details of the DPO: [Name/Email]\n5. Likely consequences of the breach: [Describe]\n6. Measures taken or proposed to address the breach: [Describe]"
            },

            # --- VENDORS ---
            {
                "title": "Vendor Security Questionnaire",
                "description": "Questions to ask new vendors before onboarding.",
                "category": "vendor",
                "filename": "vendor_questionnaire.txt",
                "content": "VENDOR SECURITY QUESTIONNAIRE\n\n1. Do you have an ISO 27001 or SOC 2 Type II certification?\n2. How do you encrypt data at rest and in transit?\n3. Do you enforce MFA for your employees?\n4. What is your SLA for notifying us of a data breach?\n5. Where is our data hosted (geographically)?"
            },
            {
                "title": "Data Processing Agreement (DPA) Checklist",
                "description": "Checklist to ensure a vendor DPA covers GDPR requirements.",
                "category": "vendor",
                "filename": "dpa_checklist.txt",
                "content": "DPA CHECKLIST (GDPR Article 28)\n\n[ ] Subject matter and duration of processing defined\n[ ] Nature and purpose of processing defined\n[ ] Type of personal data and categories of data subjects defined\n[ ] Vendor must process only on documented instructions\n[ ] Confidentiality obligations for personnel\n[ ] Security measures (Art. 32) specified\n[ ] Sub-processor authorization required\n[ ] Assistance with data subject rights\n[ ] Deletion/return of data at end of contract\n[ ] Audit rights granted to the controller"
            },

            # --- OTHER / COMPLIANCE ---
            {
                "title": "Record of Processing Activities (RoPA) Template",
                "description": "GDPR Article 30 spreadsheet template.",
                "category": "other",
                "filename": "ropa_template.csv",
                "content": "Processing Activity,Purpose,Data Subject Category,Data Category,Recipients,Retention Period,Security Measures\nHR Payroll,Pay employees,Employees,Bank details & Tax ID,Bank & Tax Authority,7 years,Encrypted database\nMarketing Emails,Send newsletters,Prospects,Name & Email,Email Provider,Until opt-out,Consent management system"
            },
            {
                "title": "NIS2 Compliance Gap Assessment",
                "description": "Checklist for the EU NIS2 Directive requirements.",
                "category": "other",
                "filename": "nis2_gap_assessment.txt",
                "content": "NIS2 GAP ASSESSMENT\n\n1. Governance & Risk Management\n[ ] Board members trained on cybersecurity\n[ ] Risk management policy approved\n\n2. Incident Handling\n[ ] 24-hour early warning capability\n[ ] 72-hour incident notification capability\n\n3. Supply Chain Security\n[ ] Security requirements in all supplier contracts\n\n4. Business Continuity\n[ ] Backups tested regularly\n[ ] Crisis management plan in place"
            }
        ]

        count_created = 0
        for t in templates:
            if DocumentTemplate.objects.filter(title=t["title"]).exists():
                continue

            doc = DocumentTemplate(
                title=t["title"],
                description=t["description"],
                category=t["category"],
                uploaded_by=admin_user
            )
            doc.file.save(t["filename"], ContentFile(t["content"].encode("utf-8")))
            doc.save()
            self.stdout.write(self.style.SUCCESS(f"  [+] Created: {t['title']}"))
            count_created += 1

        if count_created == 0:
            self.stdout.write(self.style.WARNING("Todos os templates já existiam na biblioteca."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Concluído! {count_created} novos templates adicionados."))
