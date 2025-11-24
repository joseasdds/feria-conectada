#!/usr/bin/env bash
set -euo pipefail

# Variables por defecto (se pueden pasar via env)
DB_HOST="${DB_HOST:-}"
DB_PORT="${DB_PORT:-}"
DATABASE_URL="${DATABASE_URL:-}"
REDIS_URL="${REDIS_URL:-}"
MIGRATE="${MIGRATE:-true}"
COLLECT_STATIC="${COLLECT_STATIC:-false}"
WAIT_TIMEOUT="${WAIT_TIMEOUT:-60}"

term_handler() {
  echo "Recibida seÃ±al de terminaciÃ³n. Reenviando a procesos hijos..."
  if [[ -n "${child_pid:-}" ]]; then
    kill -TERM "$child_pid" 2>/dev/null || true
    wait "$child_pid" || true
  fi
  exit 0
}
trap term_handler SIGTERM SIGINT

wait_for_host() {
  local host="$1"
  local port="$2"
  local timeout="$3"
  local start ts elapsed
  start=$(date +%s)
  echo "Esperando a $host:$port (timeout ${timeout}s)..."

  if ! command -v nc &> /dev/null; then
    echo "Advertencia: netcat (nc) no encontrado. Intentando instalar..."
    if command -v apt-get &> /dev/null; then
      apt-get update && apt-get install -y netcat
    elif command -v apk &> /dev/null; then
      apk add --no-cache netcat-openbsd
    else
      echo "ERROR: no se pudo instalar netcat. Abortando."
      exit 1
    fi
  fi

  while true; do
    if nc -z "$host" "$port" >/dev/null 2>&1; then
      echo "$host:$port disponible."
      return 0
    fi
    ts=$(date +%s)
    elapsed=$((ts - start))
    if [ "$elapsed" -ge "$timeout" ]; then
      echo "Timeout esperando a $host:$port (${timeout}s)."
      return 1
    fi
    sleep 0.5
  done
}

# Si DATABASE_URL estÃ¡ presente, extraer host:port
if [ -z "$DB_HOST" ] && [ -n "$DATABASE_URL" ]; then
  host_port="$(echo "$DATABASE_URL" | awk -F@ '{print $2}' | awk -F/ '{print $1}')"
  DB_HOST="$(echo "$host_port" | cut -d: -f1)"
  DB_PORT="$(echo "$host_port" | cut -d: -f2)"
fi

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"

if ! wait_for_host "$DB_HOST" "$DB_PORT" "$WAIT_TIMEOUT"; then
  echo "ERROR: La base de datos $DB_HOST:$DB_PORT no respondiÃ³. Abortando."
  exit 1
fi

if [ -n "$REDIS_URL" ]; then
  redis_host_port="$(echo "$REDIS_URL" | sed -E 's@^[^:]+://@@' | cut -d/ -f1)"
  REDIS_HOST="$(echo "$redis_host_port" | cut -d: -f1)"
  REDIS_PORT="$(echo "$redis_host_port" | cut -d: -f2)"
  REDIS_HOST="${REDIS_HOST:-redis}"
  REDIS_PORT="${REDIS_PORT:-6379}"

  if ! wait_for_host "$REDIS_HOST" "$REDIS_PORT" "$WAIT_TIMEOUT"; then
    echo "WARNING: Redis $REDIS_HOST:$REDIS_PORT no respondiÃ³ en ${WAIT_TIMEOUT}s. Continuando."
  fi
fi

if [ "$MIGRATE" = "true" ] || [ "$MIGRATE" = "1" ]; then
  echo "Ejecutando migraciones..."
  python manage.py migrate --noinput
fi

if [ "$COLLECT_STATIC" = "true" ] || [ "$COLLECT_STATIC" = "1" ]; then
  echo "Ejecutando collectstatic..."
  python manage.py collectstatic --noinput
fi

echo "Iniciando Gunicorn..."
exec gunicorn "feria_conectada.wsgi:application" \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --log-level info \
  --timeout 120
