"""enrich_requirements — populate real descriptions for GRC requirements.

Idempotent: only fills empty descriptions, never overwrites existing.

Run:  python manage.py enrich_requirements
"""

from django.core.management.base import BaseCommand
from django.db.models import Q

from apps.frameworks.models import Requirement


DESCRIPTIONS = {
    # --- SOC 2 (2023) ---
    "CC1": "Board and management demonstrate commitment to integrity, ethical values, and oversight of internal control.",
    "CC2": "Relevant internal control information is identified, captured, and communicated to enable personnel to carry out responsibilities.",
    "CC3": "Objectives are specified with sufficient clarity to enable identification and assessment of risks to those objectives.",
    "CC4": "Ongoing and separate evaluations are conducted to ascertain whether internal controls are present and functioning.",
    "CC5": "Control activities are selected and developed to mitigate risks to acceptable levels through policies and procedures.",
    "CC6": "Access to information assets is restricted to authorized users based on business need, protected by authentication, and monitored.",
    "CC7": "Systems are monitored for vulnerabilities, incidents detected and responded to, and recovery procedures tested regularly.",
    "CC8": "Changes to infrastructure, data, software, and procedures are authorized, designed, developed, configured, documented, tested, approved, and implemented.",
    "CC9": "Risks arising from vendor and business partner relationships are identified, assessed, and managed throughout the relationship.",
    "A1": "Systems are available for operation and use as committed or agreed, with capacity managed, backups tested, and recovery planned.",
    "C1": "Information designated as confidential is protected throughout its lifecycle - identified, retained, and disposed of per policy.",
    "PI1": "System processing is complete, valid, accurate, timely, and authorized to meet objectives, with inputs validated and outputs reviewed.",
    "P1": "Personal information is collected, used, retained, disclosed, and disposed of per privacy commitments and applicable regulations.",

    # --- GDPR ---
    "Art.5": "Personal data must be processed lawfully, fairly, transparently, for specified purposes, minimized, accurate, retained only as needed, and secured.",
    "Art.6": "Processing is lawful only if at least one of six legal bases applies: consent, contract, legal obligation, vital interests, public task, or legitimate interests.",
    "Art.7": "Consent must be freely given, specific, informed, unambiguous, and demonstrable; the data subject may withdraw it at any time.",
    "Art.12": "Controllers must provide information and communications about processing in a concise, transparent, intelligible, and easily accessible form.",
    "Art.13": "When collecting data directly from the subject, provide controller identity, purposes, legal basis, recipients, retention period, and rights.",
    "Art.14": "When data is not obtained directly, provide the same information plus the source and categories of data within one month.",
    "Art.15": "Data subjects have the right to obtain confirmation, access, and a copy of their personal data plus information about processing.",
    "Art.16": "Data subjects have the right to obtain rectification of inaccurate personal data without undue delay.",
    "Art.17": "Data subjects have the right to erasure ('right to be forgotten') when data is no longer necessary, consent withdrawn, or processing unlawful.",
    "Art.18": "Data subjects have the right to obtain restriction of processing in specific cases while the controller verifies accuracy or lawfulness.",
    "Art.20": "Data subjects have the right to receive and transmit their data in a structured, commonly used, machine-readable format.",
    "Art.24": "The controller must implement appropriate technical and organizational measures to ensure and demonstrate compliance with the regulation.",
    "Art.25": "Data protection by design and by default must be embedded into processing activities and systems from the outset.",
    "Art.28": "Processors must be bound by a written contract specifying processing instructions, security measures, sub-processor rules, and audit rights.",
    "Art.30": "Controllers and processors must maintain a record of processing activities under their responsibility.",
    "Art.32": "Implement appropriate technical and organizational measures to ensure a level of security appropriate to the risk.",
    "Art.33": "Notify the supervisory authority of a personal data breach without undue delay and within 72 hours of becoming aware of it.",
    "Art.34": "Notify affected data subjects without undue delay when a breach is likely to result in high risk to their rights and freedoms.",
    "Art.35": "Conduct a Data Protection Impact Assessment before processing likely to result in high risk, especially for new technologies or large-scale processing.",
    "Art.37": "Designate a Data Protection Officer where processing is carried out by public authority, involves large-scale monitoring, or large-scale sensitive data.",

    # --- NIS2 ---
    "Art.20": "Management bodies approve and oversee cybersecurity risk-management measures and are accountable for compliance with the directive.",
    "Art.21": "Implement technical, operational, and organizational measures including risk analysis, incident handling, business continuity, supply chain security, and encryption.",
    "Art.23": "Notify significant incidents to the CSIRT or competent authority using a three-stage process (early warning 24h, notification 72h, final report 1 month).",
    "Art.24": "Use European cybersecurity certification schemes or equivalent to demonstrate compliance for ICT products, services, and processes.",
    "Art.25": "Encourage use of European and international standards for cybersecurity risk management, information security, and incident reporting.",
    "Art.27": "Establish a cybersecurity training programme covering basic cyber hygiene and role-specific training for all staff.",
    "Art.28": "Promote basic cyber hygiene practices, awareness-raising, and training in essential and important entities.",
    "Art.29": "Participate in information-sharing arrangements, including threat intelligence, indicators of compromise, and best practices, within trusted communities.",
    "Art.30": "May voluntarily notify incidents, cyber threats, or near misses that do not qualify as significant, if the notification is relevant.",
    "Art.32": "Competent authorities have supervisory powers to inspect, request information, conduct audits, and impose administrative fines for non-compliance.",

    # --- PCI DSS 4.0 ---
    "Req.1": "Define and implement network security controls (firewalls, segmentation) to protect cardholder data environment from untrusted networks.",
    "Req.2": "Change all vendor-supplied defaults and configure systems securely; maintain configuration standards for all system components.",
    "Req.3": "Protect stored account data; minimize retention by keeping only what is needed, and secure what must be kept.",
    "Req.4": "Protect cardholder data in transit with strong cryptography (TLS 1.2+) and secure protocols over open, public networks.",
    "Req.5": "Protect all systems against malware by deploying anti-malware solutions, keeping them updated, and monitoring for signs of compromise.",
    "Req.6": "Develop software securely and patch systems to address vulnerabilities; classify and prioritize critical security patches.",
    "Req.7": "Restrict access to system components and cardholder data by business need-to-know using role-based and least-privilege principles.",
    "Req.8": "Identify and authenticate all users accessing the cardholder data environment with strong authentication, including MFA for remote and administrative access.",
    "Req.9": "Restrict physical access to cardholder data, systems, and media; monitor entry points and secure storage and disposal.",
    "Req.10": "Log, monitor, and analyze all access to system components and cardholder data to support detection and investigation of anomalies.",
    "Req.11": "Test security of systems and networks regularly (vulnerability scans, penetration tests, IDS/IPS, change-detection mechanisms).",
    "Req.12": "Support information security with documented policies, risk assessments, security awareness training, and an incident response plan.",

    # --- ISO 22301 ---
    "4": "Determine internal and external issues, interested parties and their requirements, and define the scope of the BCMS (business continuity management system).",
    "5": "Top management demonstrates leadership by establishing BCMS policy, ensuring roles and responsibilities are assigned, and integrating BCMS into business processes.",
    "6": "Plan actions to address risks and opportunities, establish business continuity objectives, and plan changes to the BCMS.",
    "7": "Provide resources, competence, awareness, communication, and documented information to support the BCMS.",
    "8.2": "Conduct business impact analysis and risk assessment to identify critical activities, dependencies, and threats that could disrupt them.",
    "8.3": "Select and implement business continuity strategies and solutions (redundancy, failover, alternate sites) based on the BIA and risk assessment.",
    "8.4": "Document business continuity plans and procedures including roles, communication, escalation, and recovery steps.",
    "8.5": "Establish an exercise programme that tests, evaluates, and continually improves business continuity plans and capabilities.",
    "9": "Monitor, measure, analyze, and evaluate BCMS performance; conduct internal audits and management reviews to assess effectiveness.",
    "10": "Address non-conformities with corrective actions; continually improve the BCMS through lessons learned and innovation.",

    # --- ISO 27005 ---
    "5.1": "Establish, implement, maintain, and continually improve an information security risk management process integrated with the ISMS.",
    "5.2": "Align risk management with other information security standards (ISO 27001, ISO 27002, ISO 31000) and organizational risk management.",
    "5.3": "Identify and manage critical success factors - senior management commitment, alignment with objectives, awareness, and appropriate resourcing.",
    "6.2": "Communicate and consult with internal and external stakeholders (risk owners, business units, experts) throughout the risk management process.",
    "6.3.1": "Establish external context (legal, regulatory, market, geopolitical, threat landscape) that shapes the risk environment.",
    "6.3.2": "Establish internal context (governance, organizational structure, capabilities, culture, resources, priorities).",
    "6.3.3": "Define risk criteria - risk appetite, risk tolerance, impact and likelihood scales, acceptance thresholds, and evaluation criteria.",
    "6.4.1": "Carry out a systematic risk identification process involving stakeholders, using structured techniques (workshops, checklists, threat modelling).",
    "6.4.2": "Identify information assets, their owners, and their value; ensure the asset inventory is complete, accurate, and maintained.",
    "6.4.3": "Identify threats (natural, accidental, deliberate) and threat sources (internal, external, adversarial, non-adversarial) relevant to the assets.",
    "6.4.4": "Identify vulnerabilities (technical, organizational, physical, human) and existing controls that may mitigate or expose the assets to threats.",
    "6.5": "Determine likelihood, impact, and level of risk using qualitative, semi-quantitative, or quantitative techniques; document assumptions and dependencies.",
    "6.6": "Compare estimated risk levels with risk criteria to determine which risks need treatment; prioritize by risk score and business impact.",
    "6.7": "Select and document treatment options (avoid, reduce, transfer, accept) with associated controls; develop risk treatment plans with owners and timelines.",
    "6.8": "Formally accept residual risks after treatment, with documented sign-off by risk owners at appropriate seniority levels.",
    "6.9": "Monitor and review risks, controls, and treatment progress on an ongoing basis and through periodic reassessments.",
    "6.10": "Record and report risk management activities - risk register, treatment plans, KRI dashboards, and reports to management and stakeholders.",
}


class Command(BaseCommand):
    help = "Populate real descriptions for requirements (idempotent, only fills empty)."

    def handle(self, *args, **opts):
        updated = 0

        # 1. Real descriptions (82 requirements across 6 frameworks)
        from django.db.models import F
        for code, desc in DESCRIPTIONS.items():
            # Match: empty, NULL, OR fallback where description == title
            qs = Requirement.objects.filter(code=code).filter(
                Q(description="")
                | Q(description__isnull=True)
                | Q(description=F("title"))
            )
            n = qs.update(description=desc)
            updated += n
        self.stdout.write(self.style.SUCCESS(
            f"Real descriptions filled: {updated}"
        ))

        # 2. ISO 27001 fallback (titles are already 1-line summaries)
        iso_qs = Requirement.objects.filter(
            framework_version__framework__code="iso27001"
        ).filter(Q(description="") | Q(description__isnull=True))
        iso_count = 0
        for r in iso_qs:
            r.description = r.title
            r.save(update_fields=["description", "updated_at"])
            iso_count += 1
        self.stdout.write(self.style.SUCCESS(
            f"ISO 27001 fallback (title as description): {iso_count}"
        ))

        self.stdout.write(self.style.SUCCESS(
            f"\nTotal: {updated + iso_count} requirements enriched."
        ))