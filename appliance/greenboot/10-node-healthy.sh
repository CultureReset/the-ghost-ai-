#!/bin/bash
# If this exits non-zero, greenboot rolls the machine back to the previous
# image before the owner ever learns an update happened.
set -euo pipefail
for i in $(seq 1 30); do
  if curl -fsS --max-time 2 http://localhost:8080/healthz >/dev/null 2>&1; then
    echo "ghost-node healthy"; exit 0
  fi
  sleep 2
done
echo "ghost-node did not become healthy in 60s" >&2
exit 1
