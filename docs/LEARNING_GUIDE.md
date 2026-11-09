# InfraPilot learning guide

## 1. What problem does it solve?

When a service feels slow or unavailable, an infrastructure engineer checks the service first, then the machine and the network. InfraPilot packages a few safe checks behind HTTP endpoints so they can be repeated consistently.

## 2. The request path

An HTTP request contains a method (here `GET`) and a path such as `/health`. FastAPI matches that path to a Python function and turns the returned dictionary into JSON. `/docs` is generated from those route definitions.

## 3. Health versus diagnostics

`/health` answers “is the API process responding?” It should be fast and simple. `/diagnostics` reads CPU, memory and disk information and saves a point-in-time snapshot. Values describe the machine visible to the process: in a container, that may differ from the Windows host.

## 4. Network checks

DNS translates a name such as `example.com` into an address. TCP uses an IP address and port to establish a connection. `/network-check` resolves a single host and attempts one connection with a short timeout. A successful check proves only that this connection worked from this process at that moment; it does not prove an entire application is healthy.

## 5. Database history

SQLite is an embedded database stored in a file, which keeps the first run easy. Each snapshot is serialized as JSON and stored with a UTC timestamp. MySQL is included as an optional service to practice relational database operations, but swapping the application repository to MySQL is a later exercise.

## 6. Docker and Nginx

The Dockerfile describes a repeatable image: Python base, dependencies, application files, non-root user, and startup command. Compose connects containers on a private network. Nginx listens on host port 8080 and forwards requests to the API container by its Compose service name (`api`).

## 7. Kubernetes

A Deployment asks Kubernetes to keep two API pods running. A Service gives them a stable in-cluster address. A ConfigMap provides non-secret settings. Readiness probes decide when a pod can receive traffic; liveness probes restart a stuck container. CPU and memory requests help scheduling; limits cap usage. The demo Secret is a placeholder and is not used by app code.

For this starter, each pod gets its own temporary `emptyDir` SQLite file. That means history is not shared between replicas and disappears when a pod is replaced. This is intentional for a small local demo; a real multi-replica service needs a shared/managed database and a carefully designed persistence strategy.

## 8. Terraform and Ansible

Terraform describes cloud resources and tracks their desired state. The example declares a VPC and private subnet. `plan` previews changes; `apply` creates billable cloud resources and is deliberately outside the default checklist. Ansible connects to existing hosts and runs tasks; this playbook gathers facts and reads disk usage without changing the server.

## 9. Monitoring

Prometheus periodically requests `/metrics` and stores numeric time series. Grafana can query Prometheus and draw dashboards. The included setup is a starter configuration. Start the optional monitoring profile only after the base Compose stack works.

## 10. Practice explaining it

Be ready to explain: (1) what each endpoint proves, (2) why the API uses SQLite, (3) how Nginx finds the API, (4) readiness versus liveness, (5) where configuration versus secrets belong, and (6) which steps you ran and what evidence you observed. Be candid about any unvalidated starter configuration.
