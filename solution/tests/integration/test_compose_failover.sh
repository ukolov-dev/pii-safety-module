#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$project_dir"

cleanup() {
  docker compose down --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

docker compose up --build --detach --remove-orphans

attempt=0
until curl --fail --silent http://127.0.0.1:8080/health/ready >/dev/null; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 60 ]; then
    docker compose ps
    exit 1
  fi
  sleep 1
done

source_text='Клиент: Иван Петров, email ivan@example.com'
first=$(docker compose exec -T api1 python -c \
  'import json, urllib.request; body=json.dumps({"payload":"Клиент: Иван Петров, email ivan@example.com","payload_id":"ha-failover-check"}, ensure_ascii=False).encode(); request=urllib.request.Request("http://127.0.0.1:8080/process", data=body, headers={"Content-Type":"application/json"}); print(urllib.request.urlopen(request, timeout=10).read().decode())')
masked=$(FIRST_RESPONSE="$first" python3 -c \
  'import json, os; print(json.loads(os.environ["FIRST_RESPONSE"])["result"])')

docker compose stop api1

request_body=$(MASKED="$masked" python3 -c \
  'import json, os; print(json.dumps({"payload": os.environ["MASKED"], "payload_id": "ha-failover-check"}, ensure_ascii=False))')
restored=$(curl --fail --silent \
  -H 'Content-Type: application/json' \
  --data "$request_body" \
  http://127.0.0.1:8080/process)

SOURCE_TEXT="$source_text" RESTORED_RESPONSE="$restored" python3 -c \
  'import json, os; assert json.loads(os.environ["RESTORED_RESPONSE"])["result"] == os.environ["SOURCE_TEXT"]'

curl --fail --silent http://127.0.0.1:8080/health/ready >/dev/null
printf '%s\n' 'HA failover passed: api2 restored api1 state through the proxy.'
