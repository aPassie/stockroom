#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace \
  --set controller.service.type=LoadBalancer \
  --set controller.metrics.enabled=true \
  --wait

helm upgrade --install metrics-server metrics-server/metrics-server \
  --namespace kube-system --wait

helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  -f monitoring/kube-prometheus-stack-values.yaml \
  --wait --timeout 10m

kubectl apply -f k8s/namespace.yaml
kubectl apply -f monitoring/alerts.yaml

echo
echo "Ingress address:"
kubectl get svc ingress-nginx-controller -n ingress-nginx \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}{"\n"}'
