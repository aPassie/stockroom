# Stockroom

Stockroom is an inventory manager for a small shop or warehouse. You add products with a SKU, price and reorder level. Every change to stock is recorded as a movement: restock, sale, return, damaged or correction. The dashboard shows what is on hand, what it is worth, and what needs reordering.

The repository also contains everything needed to ship it: tests, containers, a GitHub Actions pipeline with Trivy, Terraform for AWS VPC + EKS, a Helm chart with Ingress and HPA, and Prometheus/Grafana monitoring.

## Presentation

- [Presentation video (MP4)](demo/stockroom-presentation.mp4)
- [Slide deck (PowerPoint)](demo/stockroom-presentation.pptx)

The presentation runs for 3 minutes 5 seconds and uses Parth's recorded narration, synced to the seven slides. The MP4 includes English subtitles and chapter markers. The PowerPoint includes the script in its speaker notes. Deployment screenshots were captured on 16 October 2026; the cluster was torn down afterwards.

```
 git push ──> GitHub Actions
                ├─ pytest, frontend build, helm lint
                ├─ docker build backend + frontend
                ├─ Trivy (fails on fixable HIGH/CRITICAL)
                ├─ push ghcr.io/<owner>/stockroom-{backend,frontend}:<commit-sha>
                └─ helm upgrade --install on EKS
                                   │
 Terraform: VPC (2 public + 2 private subnets, NAT) ── EKS + managed node group
                                   │
 browser ──> ingress-nginx ──┬── /     ──> frontend Service ──> nginx pods (2)
                             └── /api  ──> backend Service  ──> FastAPI pods (2-6, HPA)
                                                                     │
                                         Prometheus ◄── /metrics     └──> PostgreSQL StatefulSet + PVC
                                             │
                                          Grafana
```

## Stack

| Layer | Tools |
|---|---|
| Frontend | React 18, Vite, plain CSS, served by `nginx-unprivileged` |
| Backend | FastAPI, SQLAlchemy 2, Alembic, psycopg 3, Prometheus instrumentator |
| Database | PostgreSQL 16 |
| Tests | pytest + FastAPI TestClient against in-memory SQLite |
| Delivery | Docker, Docker Compose, GitHub Actions, Trivy, GHCR |
| Infrastructure | Terraform (`terraform-aws-modules/vpc`, `terraform-aws-modules/eks`) |
| Platform | Kubernetes, Helm, ingress-nginx, metrics-server, HPA |
| Observability | kube-prometheus-stack (Prometheus, Grafana), ServiceMonitor, PrometheusRule |

## API

| Method | Path | |
|---|---|---|
| GET | `/health` | Liveness, no dependencies |
| GET | `/ready` | Readiness, runs `SELECT 1`, returns 503 when the DB is unreachable |
| GET | `/metrics` | Prometheus metrics |
| GET | `/api/products` | List products. Filters: `q`, `category`, `low_stock=true` |
| POST | `/api/products` | Create. SKU is upper-cased and must be unique (409 otherwise) |
| GET | `/api/products/{id}` | One product |
| PUT | `/api/products/{id}` | Update name, category, price, reorder level |
| DELETE | `/api/products/{id}` | Delete a product and its history |
| GET | `/api/products/{id}/movements` | Stock history for a product |
| POST | `/api/products/{id}/movements` | Record a movement. Rejects anything that would take stock below zero |
| GET | `/api/movements` | Latest movements across all products |
| GET | `/api/stats` | Totals, inventory value, low stock and out of stock counts, per-category units |

Quantity cannot be set directly through `PUT`. It only changes through movements, so the history always adds up to the current stock.

Swagger UI is at `/docs` on the backend.

## Run locally

```bash
docker compose up --build
```

| URL | |
|---|---|
| http://localhost:3000 | App |
| http://localhost:8000/docs | API docs |
| http://localhost:8000/metrics | Metrics |

Postgres starts first, the backend runs `alembic upgrade head` and waits until `/ready` passes, and then the frontend starts. `docker compose down -v` removes the database volume.

Some sample data:

```bash
curl -X POST localhost:8000/api/products -H 'content-type: application/json' \
  -d '{"sku":"KB-101","name":"Mechanical Keyboard","category":"Peripherals","unit_price":"3499","quantity":24,"reorder_level":8}'
curl -X POST localhost:8000/api/products/1/movements -H 'content-type: application/json' \
  -d '{"change":-3,"reason":"SALE","note":"INV-1042"}'
```

### Without Docker

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export DATABASE_URL=postgresql+psycopg://stockroom:stockroom@localhost:5432/stockroom
alembic upgrade head
uvicorn app.main:app --reload
```

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173, proxies /api to :8000
```

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest -v
```

The 22 tests cover health, readiness, metrics, product CRUD, validation, duplicate SKUs, filters, stock movements (including the no-negative-stock rule) and stats. `tests/conftest.py` swaps the database dependency for an in-memory SQLite engine, so the tests never touch Postgres.

## Containers

- `backend/Dockerfile` is a two-stage build. Dependencies install in a builder stage, and the runtime runs as UID 10001. `entrypoint.sh` runs migrations and then `exec`s uvicorn. Set `RUN_MIGRATIONS=false` to skip them.
- `frontend/Dockerfile` builds with Node and serves `dist/` from `nginx-unprivileged`, which runs as UID 101 on port 8080. The `/api` proxy target comes from `BACKEND_URL` through nginx's template support, so one image works in Compose and in Kubernetes.
- Migrations take a Postgres advisory lock, so several backend replicas starting at the same time don't race each other.

## CI/CD

`.github/workflows/ci-cd.yml` runs on every push and pull request to `main`.

1. **backend-tests**, **frontend-build**, **helm-lint** run in parallel. A failing test stops the pipeline.
2. **images** (matrix: backend, frontend) builds each image tagged with `github.sha`. It writes a full Trivy report as an artifact, then runs a second Trivy pass that fails the job on fixable HIGH/CRITICAL findings. Only then does it push to GHCR. Pull requests build and scan but don't push.
3. **deploy** runs `helm upgrade --install` on EKS with the new SHA tags and waits for the rollout.

To set it up:

| Where | Name | Value |
|---|---|---|
| Settings → Secrets → Actions | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | An IAM user allowed to call `eks:DescribeCluster` |
| Settings → Secrets → Actions | `POSTGRES_PASSWORD` | Database password for the cluster |
| Settings → Variables → Actions | `EKS_CLUSTER_NAME` | `stockroom-dev-eks` (from `terraform output cluster_name`) |
| Settings → Variables → Actions | `AWS_REGION` | `ap-south-1` |

The deploy job is skipped until `EKS_CLUSTER_NAME` is set, so the pipeline stays green before the cluster exists. Add the deploy user's ARN to `cluster_admin_arns` in Terraform so it can talk to the cluster.

After the first push, open each package under your GitHub profile → Packages and set its visibility to public. Otherwise, add an `imagePullSecret` so EKS can pull it.

Postgres only reads `POSTGRES_PASSWORD` when it initialises an empty volume. Changing the secret later won't change the password of an existing database.

### Trivy

Trivy scans the OS packages in each image (Debian for the backend, Alpine for the frontend) and the language dependencies it finds: Python packages in `site-packages`, and nothing for the frontend, because only static files ship. The gate uses `ignore-unfixed: true`, so a build fails only for HIGH/CRITICAL issues that have a patched version available. Both Dockerfiles upgrade OS packages at build time to keep that list short. The full report, including LOW/MEDIUM findings, is attached to each run as the `trivy-backend` and `trivy-frontend` artifacts.

## Terraform (AWS)

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars   # edit cluster_admin_arns
terraform init
terraform plan
terraform apply                                  # ~15 min
aws eks update-kubeconfig --region ap-south-1 --name stockroom-dev-eks
```

This creates:

- a VPC `10.40.0.0/16` across 2 AZs, with 2 public subnets (tagged for internet-facing load balancers), 2 private subnets and a single NAT gateway
- EKS 1.31 with public API endpoint, core add-ons and the EBS CSI driver (needed for the Postgres PVC)
- a managed node group of `t3.medium`, 2 to 4 nodes, in the private subnets

`terraform.tfvars` is gitignored. Credentials come from your AWS CLI profile, never from files in the repo.

A NAT gateway and 2 nodes cost money every hour. When you're done:

```bash
helm uninstall stockroom -n stockroom
helm uninstall ingress-nginx -n ingress-nginx   # removes the AWS load balancer first
terraform destroy
```

## Kubernetes

Install the cluster add-ons once (ingress-nginx, metrics-server, kube-prometheus-stack), then the namespace and alert rules:

```bash
./scripts/bootstrap-cluster.sh
```

Deploy the app. CI does this on every push to `main`, but you can also run it by hand:

```bash
kubectl apply -f k8s/namespace.yaml
helm upgrade --install stockroom helm/stockroom -n stockroom \
  -f helm/stockroom/values-prod.yaml \
  --set backend.image.repository=ghcr.io/<owner>/stockroom-backend \
  --set frontend.image.repository=ghcr.io/<owner>/stockroom-frontend \
  --set backend.image.tag=<sha> --set frontend.image.tag=<sha> \
  --set postgres.password=<password>

kubectl get pods,svc,ingress,hpa -n stockroom
helm list -n stockroom
```

On EKS, `values-prod.yaml` leaves the Ingress host empty, so the app answers on the load balancer hostname from `kubectl get ingress -n stockroom`. For a local cluster, keep the default `stockroom.local` and add it to `/etc/hosts`.

What the chart creates:

| Resource | |
|---|---|
| Deployment + ClusterIP Service `stockroom-backend` | 2+ replicas, startup/readiness/liveness probes, read-only root FS, non-root, waits for Postgres in an init container |
| Deployment + ClusterIP Service `stockroom-frontend` | 2 replicas, non-root nginx |
| StatefulSet + headless Service `stockroom-postgres` | 1 replica with a PVC from `volumeClaimTemplates` |
| Secret `stockroom-db` | DB credentials and `DATABASE_URL`. Pods restart when it changes (checksum annotation) |
| Ingress | `/api` → backend, `/` → frontend |
| HorizontalPodAutoscaler | backend, 2 to 6 replicas, 60% CPU target |
| ServiceMonitor + Grafana dashboard ConfigMap | picked up by kube-prometheus-stack |

`values-dev.yaml` drops to 1 replica each and turns off HPA and monitoring, for a quick local cluster.

Rollback: `helm history stockroom -n stockroom` then `helm rollback stockroom <revision> -n stockroom`.

### Autoscaling demo

```bash
kubectl get hpa -n stockroom -w
URL=http://<ingress-host> ./scripts/load-test.sh     # 20 workers for 3 minutes
```

On a kind cluster with 15 workers, CPU reached 385% of the request within a minute and the backend went from 2 to 6 pods.

## Monitoring

```bash
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3001:80   # admin / change-me
```

- Prometheus → Status → Targets shows `serviceMonitor/stockroom/stockroom-backend` with one `UP` endpoint per backend pod.
- Grafana → Dashboards → **Stockroom** has panels for requests/s, p50/p95/p99 latency, 5xx error rate, responses by status, backend CPU per pod, HPA replica count, and units moved per hour by reason (`stockroom_stock_units_moved_total`, a custom counter incremented on every stock movement).
- `monitoring/alerts.yaml` adds three alerts: backend down, error rate above 5%, and p95 latency above 1s.

The same dashboard JSON is in `monitoring/grafana-dashboard.json` for manual import.

## Troubleshooting lab

`troubleshooting/` has four deliberately broken manifests: a missing image tag, a Service whose selector matches nothing, a backend pointed at the wrong database host, and a memory limit low enough to get OOM-killed. [troubleshooting/README.md](troubleshooting/README.md) walks through diagnosing and fixing each one with `kubectl`.

## Layout

```
backend/            FastAPI app, Alembic migrations, tests, Dockerfile
frontend/           React app, nginx template, Dockerfile
docker-compose.yml  postgres + backend + frontend
.github/workflows/  CI/CD pipeline
terraform/          VPC + EKS
k8s/                namespace
helm/stockroom/     application chart
monitoring/         kube-prometheus-stack values, alerts, dashboard
scripts/            cluster bootstrap, load test
troubleshooting/    broken manifests and walkthrough
```
