# InfraPilot

InfraPilot is an infrastructure engineering project for diagnostics, deployment, and operations. It exposes a FastAPI service, stores diagnostic snapshots in SQLite locally and in private RDS MySQL in AWS, and exposes health and host metrics. The local stack runs with Docker Compose and Nginx; the AWS portfolio deployment uses Terraform, EC2, ECR, RDS, Secrets Manager, IAM, and Systems Manager.

> Current status: deployed and verified in AWS `ap-south-1` as a single-server portfolio environment. The public HTTP endpoint exposes only `/health`; administration uses Systems Manager. This is not production-ready or an American Express system. Never put real credentials in this repository.

## What you will learn

| Part | Purpose | Status |
|---|---|---|
| FastAPI API | HTTP endpoints, validation, health checks | implemented |
| Host diagnostics | CPU, memory, disk, uptime, DNS, TCP checks | implemented; host/container scope depends on where it runs |
| SQLite history | Save snapshots without external services | implemented |
| Automated tests | Exercise API behavior without Docker | 6 tests passed in WSL and GitHub Actions |
| Docker and Nginx | Run the API behind a reverse proxy | Compose stack started and health endpoint verified |
| MySQL | Local connectivity and persistent AWS history | RDS MySQL 8.4.11 connectivity verified; diagnostics snapshot written and returned by history |
| Kubernetes | Deployment, Service, ConfigMap, Secret template | Docker Desktop cluster; two replicas rolled out and health endpoint verified |
| Terraform | Provision AWS network and portfolio resources | Applied in `ap-south-1`; network, private RDS, ECR, IAM/SSM, and EC2 created |
| Ansible | Read-only Linux infrastructure audit | WSL audit passed with `changed=0` |
| Prometheus/Grafana | Metrics collection and dashboard | Prometheus target UP; CPU, memory, and disk panels populated in Grafana |
| GitHub Actions | Run tests on pushes and pull requests | Passed after AWS deployment and bootstrap fix commits |

## Architecture

```text
Browser / curl
      |
    Nginx :8090 (Compose)
      |
 FastAPI :8000 ---- SQLite volume (local history)
      |
 /health, /metrics, /diagnostics, /network-check, /history

Optional Compose services: MySQL, Prometheus, Grafana
Local cluster: Kubernetes Deployment + Service

AWS (ap-south-1): Internet -> EC2 Nginx :80 (/health only) -> FastAPI
                                             |
                                             +-> private RDS MySQL (diagnostic history)
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
Invoke-RestMethod http://127.0.0.1:8090/health
docker compose logs api nginx
docker compose down
```

The API history remains in SQLite inside a named volume. MySQL is provided as an adjacent database service for connectivity practice; this version does not claim to persist its application history in MySQL.

Start the optional MySQL container with `docker compose --profile database up --build -d`. Start Prometheus and Grafana with `docker compose --profile monitoring up --build -d`; visit `http://localhost:9090` and `http://localhost:3001` (the host port for Grafana may differ if 3000 is busy; change the local demo password before shared use). Combine profiles with `docker compose --profile database --profile monitoring up --build -d`.

## Kubernetes (Docker Desktop)

Start the Kubernetes cluster in Docker Desktop and make sure `kubectl` uses the `docker-desktop` context. Build the image and apply the manifests:

```powershell
docker build -t infrapilot:local .
kubectl apply -f k8s/
kubectl -n infrapilot rollout status deployment/infrapilot
kubectl -n infrapilot get pods,svc
kubectl -n infrapilot port-forward service/infrapilot 8001:8000
```

In another window call `http://127.0.0.1:8001/health`. The manifests use a demo secret value: replace it before any shared environment. Stop the port forward with Ctrl+C and scale the Deployment to zero when you want to stop its pods.

## Infrastructure examples

- `terraform/` contains the AWS portfolio deployment: VPC, public EC2 host, private RDS MySQL, ECR, Secrets Manager, and IAM/SSM access. It is currently deployed in `ap-south-1`. Follow [AWS deployment](docs/AWS_DEPLOYMENT.md) to inspect, operate, and clean up the stack.
- `ansible/` contains a read-only Linux facts playbook. It was run successfully against Ubuntu in WSL (`changed=0`).
- `monitoring/` contains Prometheus scrape configuration and Grafana provisioning. Prometheus showed the API target UP and the Grafana dashboard showed CPU, memory, and disk metrics locally.

## Learn the code in this order

1. `app/main.py`: routes are the URLs clients call.
2. `app/diagnostics.py`: read-only OS and network inspection.
3. `app/storage.py`: SQLite schema and snapshot persistence.
4. `tests/`: requests sent to the API and expected responses.
5. `Dockerfile` and `compose.yaml`: how processes and services are packaged and connected.
6. `nginx/default.conf`: how the proxy forwards HTTP requests.
7. `k8s/`: Kubernetes desired state, service discovery, and probes.
8. `terraform/` and `ansible/`: infrastructure provisioning versus host configuration.

See `docs/LEARNING_GUIDE.md` for a guided walkthrough, `docs/OPERATIONS.md` for local troubleshooting, and `docs/AWS_DEPLOYMENT.md` for the staged cloud deployment.

## Honest portfolio description

Six tests passed in WSL and GitHub Actions. Docker Compose and local MySQL connectivity were verified; two Kubernetes replicas rolled out; Prometheus scraped the API and Grafana displayed host metrics; Terraform applied the AWS stack; and the read-only Ansible audit passed against WSL. In AWS, the EC2 public `/health` endpoint returned `status: ok`; an SSM session verified RDS MySQL 8.4.11 connectivity, wrote a diagnostic snapshot, and read it back from `/history`. The AWS deployment is a single EC2 host with HTTP only, no high availability, and no production security or disaster-recovery claim.
