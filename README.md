# InfraPilot 2.0

InfraPilot is a learning project for infrastructure operations. It exposes a small FastAPI service that reports its own health and gathers safe, read-only host diagnostics. It stores diagnostic snapshots in SQLite. Docker Compose adds Nginx and MySQL; Kubernetes, Terraform, Ansible, monitoring, and CI files demonstrate deployment patterns and are described with their current validation status.

> This is a local portfolio demo, not a production-ready or American Express system. Never put real credentials in this repository.

## What you will learn

| Part | Purpose | Status |
|---|---|---|
| FastAPI API | HTTP endpoints, validation, health checks | implemented |
| Host diagnostics | CPU, memory, disk, uptime, DNS, TCP checks | implemented; host/container scope depends on where it runs |
| SQLite history | Save snapshots without external services | implemented |
| Automated tests | Exercise API behavior without Docker | included |
| Docker and Nginx | Run the API behind a reverse proxy | configured |
| MySQL | Optional service and connectivity example | configured; API history currently uses SQLite |
| Kubernetes | Deployment, Service, ConfigMap, Secret template | starter manifests; not yet locally validated |
| Terraform and Ansible | Infrastructure and host-audit examples | starter examples; not yet applied |
| Prometheus/Grafana | Metrics collection and dashboard provisioning | optional starter configuration |
| GitHub Actions | Run tests on pushes and pull requests | configured; not yet observed on GitHub |

## Architecture

```text
Browser / curl
      |
    Nginx :8080 (Compose)
      |
 FastAPI :8000 ---- SQLite volume (diagnostic history)
      |
 /health, /metrics, /diagnostics, /network-check, /history

Optional Compose services: MySQL, Prometheus, Grafana
Optional local cluster: Kubernetes Deployment + Service
```

## Start on Windows (PowerShell)

Install Python 3.12 and Git. In PowerShell, if Python is not installed, run `winget install --id Python.Python.3.12 -e` and then open a new PowerShell window. Docker Desktop is needed only for the container section. Open PowerShell in this folder.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

In a second PowerShell window, try:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/diagnostics
Invoke-RestMethod 'http://127.0.0.1:8000/network-check?host=example.com&port=443'
Invoke-RestMethod http://127.0.0.1:8000/history
```

Open `http://127.0.0.1:8000/docs` for the interactive API guide. Stop the server with Ctrl+C.

### Run the tests

```powershell
python -m pytest -q
```

Tests use a temporary SQLite file and do not require Docker, MySQL, or internet connectivity.

## Run the container stack

Copy `.env.example` to `.env` and replace the demo passwords before using MySQL. These values are for local learning only.

```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose ps
Invoke-RestMethod http://127.0.0.1:8080/health
docker compose logs api nginx
docker compose down
```

The API history remains in SQLite inside a named volume. MySQL is provided as an adjacent database service for connectivity practice; this version does not claim to persist its application history in MySQL.

Start the optional MySQL container with `docker compose --profile database up --build -d`. Start Prometheus and Grafana with `docker compose --profile monitoring up --build -d`; visit `http://localhost:9090` and `http://localhost:3000` (Grafana's local demo defaults are admin/admin; change them before any shared use). Combine profiles with `docker compose --profile database --profile monitoring up --build -d`.

## Kubernetes (Kind)

Install Docker Desktop, `kind`, and `kubectl`. Build and load the image into a local Kind cluster:

```powershell
kind create cluster --name infra-pilot
docker build -t infrapilot:local .
kind load docker-image infrapilot:local --name infra-pilot
kubectl apply -f k8s/
kubectl -n infrapilot get pods,svc
kubectl -n infrapilot port-forward service/infrapilot 8000:8000
```

In another window call `http://127.0.0.1:8000/health`. The manifests use a demo secret value: replace it before any shared environment. Cleanup: `kind delete cluster --name infra-pilot`.

## Infrastructure examples

- `terraform/` contains a small AWS VPC example. Review and run `terraform fmt -check` and `terraform validate` only after installing Terraform and initializing the directory. `terraform plan` may need AWS credentials and can incur cost only if you apply it; do not apply without reviewing the plan.
- `ansible/` contains a read-only Linux facts playbook. From a Linux host with Ansible and an SSH target configured, run `ansible-playbook -i inventory.ini audit.yml --check`. This is an example, not a verified run against a real server.
- `monitoring/` contains Prometheus scrape configuration and a Grafana provisioning stub. Optional Compose profiles can run these tools locally.

## Learn the code in this order

1. `app/main.py`: routes are the URLs clients call.
2. `app/diagnostics.py`: read-only OS and network inspection.
3. `app/storage.py`: SQLite schema and snapshot persistence.
4. `tests/`: requests sent to the API and expected responses.
5. `Dockerfile` and `compose.yaml`: how processes and services are packaged and connected.
6. `nginx/default.conf`: how the proxy forwards HTTP requests.
7. `k8s/`: Kubernetes desired state, service discovery, and probes.
8. `terraform/` and `ansible/`: infrastructure provisioning versus host configuration.

See `docs/LEARNING_GUIDE.md` for a guided walkthrough and `docs/OPERATIONS.md` for troubleshooting and the application deadline plan.

## Honest portfolio description

In this build environment, the five unit tests pass and Python syntax compilation passes. Live HTTP, Docker, Kind, AWS, Ansible and monitoring validation could not be completed here. After you personally run and verify the relevant steps, a truthful description could be: “Built InfraPilot, a FastAPI infrastructure diagnostics demo with read-only host and TCP/DNS checks, SQLite incident history, automated unit tests, Docker/Nginx deployment configuration, and starter Kubernetes/Terraform/Ansible examples.” Do not claim AWS deployment, production readiness, MySQL-backed app persistence, Kubernetes validation, or monitoring validation until personally completed and evidenced.
