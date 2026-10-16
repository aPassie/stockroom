# Troubleshooting lab

Each manifest breaks something on purpose. Replace `your-github-user` with your GHCR owner first, apply one, find the cause using only `kubectl`, fix it, then delete it.

```bash
kubectl apply -f troubleshooting/01-bad-image-tag.yaml
kubectl delete -f troubleshooting/01-bad-image-tag.yaml
```

## 1. Image tag that does not exist

Symptom: pod stuck in `ErrImagePull` / `ImagePullBackOff`.

```bash
kubectl get pods -n stockroom -l app=backend-canary
kubectl describe pod -n stockroom -l app=backend-canary | tail -15
```

The events show `not found` for `v9.9.9`. CI pushes the commit SHA and `latest`, so point it at one of those:

```bash
kubectl set image deploy/stockroom-backend-canary -n stockroom backend=ghcr.io/<owner>/stockroom-backend:<sha>
```

A `401 Unauthorized` instead of `manifest unknown` means the GHCR package is private. Make it public or add an `imagePullSecret`.

## 2. Service with no endpoints

Symptom: the Service exists but requests to it time out.

```bash
kubectl get endpointslices -n stockroom -l kubernetes.io/service-name=stockroom-api-internal
kubectl get pods -n stockroom --show-labels | grep backend
```

The selector asks for `component=api`, but backend pods are labelled `component=backend`. No matching labels means no endpoints. Fix the selector:

```bash
kubectl patch svc stockroom-api-internal -n stockroom \
  -p '{"spec":{"selector":{"app.kubernetes.io/component":"backend"}}}'
```

## 3. Wrong database host

Symptom: pod is `Running` but `0/1 READY`, and the container restarts.

```bash
kubectl logs -n stockroom stockroom-backend-debug
kubectl describe pod -n stockroom stockroom-backend-debug
```

The logs show `failed to resolve host 'postgres'`. The in-cluster Service is `stockroom-postgres`, and the password is not `change-me` outside local dev. Read the URL from the chart's secret instead of hardcoding it:

```yaml
env:
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: stockroom-db
        key: DATABASE_URL
```

This is also why `/ready` checks the database: the pod never gets traffic while it can't reach PostgreSQL.

```bash
kubectl get svc -n stockroom
```

## 4. Memory limit too low

Symptom: `OOMKilled`, then `CrashLoopBackOff`.

```bash
kubectl get pod -n stockroom stockroom-backend-tiny
kubectl describe pod -n stockroom stockroom-backend-tiny | grep -A3 "Last State"
```

`Reason: OOMKilled` with exit code 137. Python with FastAPI and SQLAlchemy needs about 80 MiB at idle. The chart uses a 128Mi request and a 384Mi limit.

## Useful commands

```bash
kubectl get events -n stockroom --sort-by=.lastTimestamp
kubectl logs -n stockroom deploy/stockroom-backend --previous
kubectl rollout history deploy/stockroom-backend -n stockroom
helm history stockroom -n stockroom
helm rollback stockroom <revision> -n stockroom
```
