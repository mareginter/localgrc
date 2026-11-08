# 🛡️ LocalGRC

**A self-hosted, privacy-first Governance, Risk & Compliance (GRC) platform with an integrated Local AI Assistant.**

LocalGRC is designed for organizations and consultants who need a powerful GRC tool but want to keep their sensitive data entirely within their own infrastructure. No cloud, no external APIs, no data leaks. Everything runs on your LAN.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.0-092E20?logo=django&logoColor=white)

---

## ✨ Features

- **Risk Management**: 5x5 likelihood/impact matrix, risk scoring, and treatment plans.
- **Compliance Frameworks**: Pre-loaded with ISO 27001 and NIST CSF (extensible). Map controls to requirements.
- **Control Management**: Track implementation status, coverage, and evidence.
- **Policy Management**: Full versioning, approval workflows, and review dates.
- **Audits & Findings**: Track non-conformities, observations, and corrective actions.
- **Third-Party Risk (Vendors)**: Manage DPAs, vendor assessments, and criticality.
- **Incident Management**: Log incidents and track regulatory reporting deadlines (e.g., GDPR 72h).
- **Evidence Locker**: Centralized repository for compliance proof with expiry tracking.
- **🤖 Local AI Assistant**: Chat with your GRC data using a local LLM via Ollama. Ask about risks, policies, or compliance status without leaving the server.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12 / Django
- **Database**: PostgreSQL 16
- **Frontend**: Server-side rendered HTML/CSS (Modern, zero-build frontend)
- **Web Server**: Nginx
- **AI Engine**: Ollama (Llama 3.2, Nomic-Embed-Text)
- **Orchestration**: Docker & Docker Compose

---

## 🚀 Quick Start (Production / Local)

### 1. Prerequisites
- [Docker](https://docs.docker.com/get-docker/) and Docker Compose installed.
- At least **4GB of RAM** dedicated to Docker (8GB+ recommended for larger AI models).

### 2. Clone and Configure
```bash
git clone https://github.com/mareginter/localgrc.git
cd localgrc