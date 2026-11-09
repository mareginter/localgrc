from django.core.management.base import BaseCommand
from apps.frameworks.models import Requirement

ISO_DESCRIPTIONS = {
    "A.5.1": "Policies for information security shall be defined, approved by management, published and communicated to employees and relevant external parties.",
    "A.5.2": "Information security roles and responsibilities shall be defined and allocated according to organizational needs.",
    "A.6.1": "Information security roles and responsibilities shall be defined and allocated according to organizational needs.",
    "A.6.2": "A background verification check shall be carried out for all candidates for employment.",
    "A.7.1": "Physical security perimeters shall be defined and used to protect areas that contain information and other associated assets.",
    "A.8.1": "Information stored on, processed by or accessible via user endpoint devices shall be protected.",
    "A.8.2": "Information shall be classified according to the information security needs of the organization.",
    "A.8.3": "Information shall be handled in accordance with its classification.",
    "A.9.1": "Access to information and other associated assets shall be restricted based on business and security requirements.",
    "A.9.2": "User access to systems and services shall be formally managed through the entire lifecycle.",
    "A.10.1": "Cryptographic controls shall be used to protect the confidentiality, integrity and authenticity of information.",
    "A.11.1": "Physical security perimeters shall be defined and used to protect areas that contain information.",
    "A.12.1": "Operational procedures shall be documented and made available to all users.",
    "A.12.2": "Networks and network devices shall be secured, managed and controlled.",
    "A.12.3": "Information shall be backed up and tested regularly.",
    "A.12.4": "Event logs shall be produced, stored, protected and analysed.",
    "A.12.5": "Software shall be installed only by authorised personnel.",
    "A.12.6": "Technical vulnerabilities shall be identified and addressed in a timely manner.",
    "A.13.1": "Information security controls for networks shall be implemented.",
    "A.13.2": "Information transferred within an organization or to external parties shall be protected.",
    "A.14.1": "Information security requirements shall be included in system development lifecycles.",
    "A.14.2": "Security shall be designed and implemented in software development.",
    "A.14.3": "Data used in testing shall be selected, protected and managed.",
    "A.15.1": "Information security requirements shall be agreed with suppliers.",
    "A.15.2": "Supplier service delivery shall be monitored and reviewed.",
    "A.16.1": "Information security incidents shall be managed and reported.",
    "A.16.2": "Information security incidents shall be assessed and classified.",
    "A.17.1": "Information security continuity shall be planned and implemented.",
    "A.17.2": "ICT readiness for business continuity shall be ensured.",
    "A.18.1": "Compliance with legal and contractual requirements shall be identified, documented and up to date.",
    "A.18.2": "Information security reviews shall be performed independently."
}

NIST_DESCRIPTIONS = {
    "ID.AM-1": "Physical devices and systems within the organization are inventoried.",
    "ID.AM-2": "Software platforms and applications within the organization are inventoried.",
    "ID.AM-3": "Organizational communication and data flows are mapped.",
    "ID.AM-4": "External information systems are catalogued.",
    "ID.AM-5": "Resources are prioritized based on their classification, criticality, and business value.",
    "ID.BE-1": "The organization's role in the supply chain is identified and communicated.",
    "ID.BE-2": "The organization's place in critical infrastructure and its industry sector is identified.",
    "ID.BE-3": "Priorities for organizational mission, objectives, and activities are established.",
    "ID.GV-1": "Organizational information security policy is established.",
    "ID.GV-2": "Information security roles and responsibilities are coordinated.",
    "ID.GV-3": "Legal and regulatory requirements regarding cybersecurity are understood and managed.",
    "ID.GV-4": "Governance and risk management processes address cybersecurity risks.",
    "ID.RA-1": "Asset vulnerabilities are identified and documented.",
    "ID.RA-2": "Cyber threat intelligence is received from information sharing forums.",
    "ID.RA-3": "Threats, both internal and external, are identified and documented.",
    "ID.RA-4": "Potential business impacts and likelihoods are identified.",
    "ID.RA-5": "Threats, vulnerabilities, likelihoods, and impacts are used to determine risk.",
    "ID.RA-6": "Risk responses are identified and prioritized.",
    "ID.RM-1": "Risk management processes are established and managed.",
    "ID.RM-2": "Organizational risk tolerance is determined and clearly expressed.",
    "ID.RM-3": "Determination of risk tolerance is informed by the organization's role.",
    "PR.AC-1": "Identities and credentials are issued, managed, verified, revoked, and audited.",
    "PR.AC-2": "Physical access to assets is managed and protected.",
    "PR.AC-3": "Remote access is managed.",
    "PR.AC-4": "Access permissions incorporate the principles of least privilege and separation of duties.",
    "PR.AC-5": "Network integrity is protected.",
    "PR.AC-6": "Identities are proofed and bound to credentials.",
    "PR.AC-7": "Users, devices, and other assets are authenticated commensurate with the risk.",
    "PR.AT-1": "All users are informed and trained.",
    "PR.AT-2": "Privileged users understand their roles and responsibilities.",
    "PR.AT-3": "Third-party stakeholders understand their roles and responsibilities.",
    "PR.AT-4": "Senior executives understand their roles and responsibilities.",
    "PR.AT-5": "Physical and cybersecurity personnel understand their roles.",
    "PR.DS-1": "Data-at-rest is protected.",
    "PR.DS-2": "Data-in-transit is protected.",
    "PR.DS-3": "Assets are formally managed throughout removal, transfers, and disposition.",
    "PR.DS-4": "Adequate capacity to ensure availability is maintained.",
    "PR.DS-5": "Protections against data leaks are implemented.",
    "PR.DS-6": "Integrity checking mechanisms are used to verify software and information integrity.",
    "PR.DS-7": "The development and testing environment(s) are separate from production.",
    "PR.IP-1": "A baseline configuration of information technology is created and maintained.",
    "PR.IP-2": "A System Development Life Cycle to manage systems is implemented.",
    "PR.IP-3": "Configuration change control processes are in place.",
    "PR.IP-4": "Backups of information are conducted, maintained, and tested.",
    "PR.IP-5": "Policy and regulations regarding the physical environment are met.",
    "PR.IP-6": "Data is destroyed according to policy.",
    "PR.IP-7": "Protection processes are improved.",
    "PR.IP-8": "Effectiveness of protection technologies is shared.",
    "PR.IP-9": "Response and recovery plans are established and managed.",
    "PR.IP-10": "Response and recovery plans are tested.",
    "PR.IP-11": "Cybersecurity is included in human resources practices.",
    "PR.IP-12": "A vulnerability management plan is developed and implemented.",
    "PR.MA-1": "Maintenance and repair of organizational assets are performed and logged.",
    "PR.MA-2": "Remote maintenance of organizational assets is approved and logged.",
    "PR.PT-1": "Audit/log records are determined, documented, implemented, and reviewed.",
    "PR.PT-2": "Removable media is protected and its use restricted.",
    "PR.PT-3": "The principle of least functionality is incorporated.",
    "PR.PT-4": "Communications and control networks are protected.",
    "PR.PT-5": "Mechanisms are implemented to achieve resilience requirements.",
    "DE.AE-1": "A baseline of network operations and expected data flows is established.",
    "DE.AE-2": "Detected events are analyzed to understand attack targets and methods.",
    "DE.AE-3": "Event data are collected and correlated from multiple sources.",
    "DE.AE-4": "Impact of events is determined.",
    "DE.AE-5": "Incident alert thresholds are established.",
    "DE.CM-1": "The network is monitored to detect potential cybersecurity events.",
    "DE.CM-2": "The physical environment is monitored to detect potential events.",
    "DE.CM-3": "Personnel activity is monitored to detect potential events.",
    "DE.CM-4": "Malicious code is detected.",
    "DE.CM-5": "Unauthorized mobile code is detected.",
    "DE.CM-6": "External service provider activity is monitored.",
    "DE.CM-7": "Monitoring for unauthorized personnel, connections, and devices is performed.",
    "DE.CM-8": "Vulnerability scans are performed.",
    "DE.DP-1": "Roles and responsibilities for detection are well defined.",
    "DE.DP-2": "Detection activities comply with all applicable requirements.",
    "DE.DP-3": "Detection processes are tested.",
    "DE.DP-4": "Event detection information is communicated.",
    "DE.DP-5": "Detection processes are continuously improved.",
    "RS.RP-1": "Response plan is executed during or after an incident.",
    "RS.CO-1": "Personnel know their roles and order of operations when a response is needed.",
    "RS.CO-2": "Incidents are reported consistent with established criteria.",
    "RS.CO-3": "Information is shared consistent with response plans.",
    "RS.CO-4": "Coordination with stakeholders occurs consistent with response plans.",
    "RS.CO-5": "Voluntary information sharing occurs with external stakeholders.",
    "RS.AN-1": "Notifications from detection systems are investigated.",
    "RS.AN-2": "The impact of the incident is understood.",
    "RS.AN-3": "Forensics are performed.",
    "RS.AN-4": "Incidents are categorized consistent with response plans.",
    "RS.MI-1": "Incidents are contained.",
    "RS.MI-2": "Incidents are mitigated.",
    "RS.MI-3": "Newly identified vulnerabilities are mitigated or accepted.",
    "RS.IM-1": "Response plans incorporate lessons learned.",
    "RS.IM-2": "Response strategies are updated.",
    "RC.RP-1": "Recovery plan is executed during or after a cybersecurity incident.",
    "RC.IM-1": "Recovery plans incorporate lessons learned.",
    "RC.IM-2": "Recovery strategies are updated.",
    "RC.CO-1": "Public relations are managed.",
    "RC.CO-2": "Reputation after an incident is repaired.",
    "RC.CO-3": "Recovery activities are communicated to internal and external stakeholders."
}

class Command(BaseCommand):
    help = "Populates descriptions for standard ISO 27001 and NIST CSF requirements."

    def handle(self, *args, **kwargs):
        self.stdout.write("A preencher descrições dos requisitos...")
        
        updated_count = 0
        reqs = Requirement.objects.all()

        for req in reqs:
            # Se já tem descrição, salta
            if req.description:
                continue

            desc = None
            # Tenta apanhar o código exato
            if req.code in ISO_DESCRIPTIONS:
                desc = ISO_DESCRIPTIONS[req.code]
            elif req.code in NIST_DESCRIPTIONS:
                desc = NIST_DESCRIPTIONS[req.code]
            
            if desc:
                req.description = desc
                req.save()
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"Concluído! {updated_count} descrições atualizadas."))
