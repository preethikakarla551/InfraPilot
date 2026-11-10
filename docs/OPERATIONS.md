# Operations and validation checklist

Purpose: a reusable checklist for validating InfraPilot locally and in its AWS portfolio deployment. It covers project setup, endpoint checks, deployment, and documentation.

## Suggested sequence

1. **First 30 minutes:** install/check Python, create venv, install requirements, run tests.
2. **Next 60–90 minutes:** start API, call every endpoint, inspect `/docs`, understand the code.
3. **Next 60 minutes:** build Docker image and verify Compose/Nginx health.
4. **Next 60–90 minutes (if tools work):** try Kind and the Kubernetes manifests; record exact results.
5. **Next 45 minutes:** review Terraform/Ansible/monitoring examples; validate only tools actually installed.
6. **Next 60 minutes:** clean README, capture a short demo, publish to GitHub if account/access is ready.
7. **At least 2 hours before deadline:** update application materials with only verified work, review the job form, and submit. Do not wait until 10 PM.

## Validation checklist

- [ ] `python -m pytest -q` passes locally.
- [ ] `/health` returns `status: ok`.
- [ ] `/diagnostics` returns CPU, memory, disk and uptime; `/history` contains the saved record.
- [ ] `/network-check` succeeds for an accessible host/port and returns a useful failure for a closed port.
- [ ] `/metrics` returns Prometheus text format.
- [ ] `docker compose up --build -d` succeeds; `/health` works through `localhost:8080`.
- [ ] If tried: MySQL, Prometheus, Grafana and Kubernetes are separately validated, with commands and outcomes recorded.
- [ ] If publishing: check repository contents, remove secrets, and verify GitHub Actions run.
- [ ] Application is submitted and confirmation saved before 10 PM IST.

## Troubleshooting

- PowerShell blocks activation: run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then activate the venv again.
- Port busy: stop the other process or change the host port in `compose.yaml`.
- Docker daemon unavailable: start Docker Desktop, wait for it to be ready, then retry.
- DNS/TCP check fails: confirm the chosen host and port are reachable from the current network; a failure is a useful diagnostic result, not an API crash.
- Linux stats look unusual in Docker: container CPU, memory and filesystem views vary by runtime; label the scope in your demo.
- Database locked or missing: stop duplicate local servers, ensure the `data` folder is writable, and check `INFRAPILOT_DB`.
