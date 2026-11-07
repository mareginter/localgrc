markdown
# Deployment — LocalGRC

## Requisitos
- Ubuntu Server 22.04+ (ou similar)
- Docker Engine 24+ e Docker Compose v2
- Servidor na LAN com IP fixo (ex. `192.168.1.50`)

## Primeira instalação

```bash
git clone https://github.com/<your-user>/localgrc.git
cd localgrc
cp .env.example .env
# Edite .env — mude POSTGRES_PASSWORD, DJANGO_SECRET_KEY, LOCALGRC_ADMIN_PASSWORD
docker compose up -d --build
A app fica disponível em http://<ip-do-servidor>:8080.
O utilizador admin inicial é o definido em .env (LOCALGRC_ADMIN_EMAIL).

Backup
bash
docker compose exec -T db pg_dump -U localgrc localgrc > backup-$(date +%F).sql
docker run --rm -v localgrc_uploads:/data -v $(pwd):/out alpine \
  tar czf /out/uploads-$(date +%F).tgz -C /data .
Restore
bash
docker compose exec -T db psql -U localgrc localgrc < backup.sql
docker run --rm -v localgrc_uploads:/data -v $(pwd):/in alpine \
  sh -c "cd /data && tar xzf /in/uploads.tgz"
Upgrade
bash
git pull
docker compose up -d --build   # migrations run automatically on start
text

### `README.md`

```markdown
# LocalGRC

Self-hosted Governance, Risk & Compliance platform — runs entirely on your LAN. No cloud, no SaaS, no data leaving the perimeter.

## Status
Sprint 0 — foundation (auth, RBAC, audit log, workflow engine, tags, comments, attachments, notifications).

## Quick start
See [`docs/deployment.md`](docs/deployment.md).

## Architecture
See [`docs/erd.md`](docs/erd.md) for the data model.

## License
AGPL-3.0 — see [LICENSE](LICENSE).
LICENSE
AGPL-3.0 — copy the canonical text from https://www.gnu.org/licenses/agpl-3.0.txt