#!/usr/bin/env bash
set -euo pipefail

URL="${URL:-http://stockroom.local}"
HOST_HEADER="${HOST_HEADER:-}"
DURATION="${DURATION:-180}"
CONCURRENCY="${CONCURRENCY:-20}"

curl_args=(-s -o /dev/null)
[[ -n "$HOST_HEADER" ]] && curl_args+=(-H "Host: $HOST_HEADER")

echo "Hitting $URL/api for ${DURATION}s with $CONCURRENCY workers"
echo "Watch: kubectl get hpa -n stockroom -w"

end=$((SECONDS + DURATION))
worker() {
  while (( SECONDS < end )); do
    curl "${curl_args[@]}" "$URL/api/stats"
    curl "${curl_args[@]}" "$URL/api/products?q=a"
    curl "${curl_args[@]}" "$URL/api/movements"
  done
}

for _ in $(seq "$CONCURRENCY"); do worker & done
wait
echo "Done"
