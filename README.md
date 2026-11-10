markdown
# 🛡️ LocalGRC

**A self-hosted, privacy-first Governance, Risk & Compliance (GRC) and Vulnerability Management platform with an integrated Local AI Assistant.**

LocalGRC is designed for organizations and consultants who need a powerful GRC tool but want to keep their sensitive data entirely within their own infrastructure. No cloud, no external APIs, no data leaks. Everything runs on your LAN.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.0-092E20?logo=django&logoColor=white)
![AI](https://img.shields.io/badge/AI-Ollama-black)

---

## ✨ Features

### 📊 Core GRC
- **Risk Management**: 5x5 likelihood/impact matrix, risk scoring, and treatment plans.
- **Compliance Frameworks**: Pre-loaded with ISO 27001 and NIST CSF requirements (with official descriptions). Map controls to requirements.
- **Control Management**: Track implementation status, coverage, and evidence.
- **Policy Management**: Full versioning, approval workflows, and review dates.
- **Audits & Findings**: Track non-conformities, observations, and corrective actions.
- **Third-Party Risk (Vendors)**: Manage DPAs, vendor assessments, and criticality.
- **Incident Management**: Log incidents and track regulatory reporting deadlines (e.g., GDPR 72h).

### 🛡️ Technical Security
- **Vulnerability Management**: Track CVEs, affected endpoints, CVSS scores, and remediation plans. Interactive dashboard with severity breakdown.
- **Evidence Locker**: Centralized repository for compliance proof with expiry tracking.
- **Document Library**: Upload and share standardized templates (policies, risk forms, audit checklists) across the team.

### 🤖 AI & Automation
- **Local AI Assistant (RAG)**: Chat with your GRC data using a local LLM. Upload PDFs (policies, manuals) and the assistant will read them and answer questions based on your internal documentation.
- **PDF Reports**: Generate professional PDF reports for Risks, Control Coverage, and Audits (with findings).
- **Automated Backups**: Daily automated database and file backups to ensure you never lose your data.

### 👥 Administration
- **Team Management**: Full RBAC (Role-Based Access Control). Create admins, staff, and standard users.
- **Premium UI**: Modern, responsive, zero-build frontend (HTML/CSS) with dashboards, KPIs, and data visualization.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12 / Django
- **Database**: PostgreSQL 16
- **Frontend**: Server-side rendered HTML/CSS (Modern, zero-build)
- **Web Server**: Nginx
- **AI Engine**: Ollama (Llama 3.2, Nomic-Embed-Text)
- **PDF Generation**: WeasyPrint
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
3. Environment Variables
Copy the example environment file and generate your secrets:

bash
cp .env.example .env
Open the .env file and change the default passwords and secrets:

POSTGRES_PASSWORD: Set a strong database password.

DJANGO_SECRET_KEY: Generate a random string.

OLLAMA_MODEL: Set to llama3.2:1b (default for 4GB RAM) or llama3.1:8b (requires 8GB+ RAM).

4. Build and Start
bash
docker compose up -d --build
5. Initialize the Database
Create the database schema and bootstrap the initial admin user/organization:

bash
docker compose exec app python manage.py migrate
docker compose exec app python manage.py bootstrap
6. Download AI Models
Before using the Assistant tab, pull the required models into the Ollama container:

bash
# The LLM for chat (small, fast, fits in 4GB RAM)
docker compose exec ollama ollama pull llama3.2:1b

# The embedding model for RAG (document search)
docker compose exec ollama ollama pull nomic-embed-text
7. Access LocalGRC
Application: http://localhost:8080

Django Admin: http://localhost:8080/admin
(Use the admin credentials defined in your .env file)

📚 Documentation
LocalGRC comes with detailed HTML manuals. Open them in your browser:

User Manual

Admin Manual

IT & DevOps Manual

⚙️ Environment Variables Reference
Variable	Default	Description
POSTGRES_PASSWORD	required	Database password.
DJANGO_SECRET_KEY	required	Django cryptographic key. Keep secret!
HTTP_PORT	8080	Port exposed by the Nginx container.
OLLAMA_MODEL	llama3.2:1b	The LLM used for the assistant.
OLLAMA_EMBED_MODEL	nomic-embed-text	Model used for vector embeddings (RAG).
DJANGO_DEBUG	false	Set to true only for local development troubleshooting.
💾 Backups
The system includes an automated backup service that runs daily. It saves the PostgreSQL database and all uploaded files to the ./backups folder on your host machine. Keep only the last 7 days of backups.

🤝 Contributing
Contributions are welcome! Whether it's reporting a bug, suggesting a feature, or submitting a Pull Request.

Fork the Project

Create your Feature Branch (git checkout -b feature/AmazingFeature)

Commit your Changes (git commit -m 'Add some AmazingFeature')

Push to the Branch (git push origin feature/AmazingFeature)

Open a Pull Request

📄 License
Distributed under the MIT License. See LICENSE for more information.