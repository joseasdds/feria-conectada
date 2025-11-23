#!/usr/bin/env bash

# Salir inmediatamente si un comando falla, si se usa una variable no definida, 
# o si falla cualquier comando en un pipe.
set -euo pipefail

# 1. DefiniciÃ³n de Variables (con valores por defecto si no estÃ¡n en .env o docker-compose)
DB_HOST="${DB_HOST:-}"
DB_PORT="${DB_PORT:-}"
DATABASE_URL="${DATABASE_URL:-}"
REDIS_URL="${REDIS_URL:-}"
MIGRATE="${MIGRATE:-true}"          # Controla si el servicio ejecuta migraciones
COLLECT_STATIC="${COLLECT_STATIC:-false}" # Controla si el servicio ejecuta collectstatic
WAIT_TIMEOUT="${WAIT_TIMEOUT:-60}"  # Tiempo mÃ¡ximo de espera para DB/Redis

# 2. Manejo de SeÃ±ales (para apagado limpio de procesos)
term_handler() {
  echo "Recibida seÃ±al de terminaciÃ³n. Reenviando a procesos hijos..."
  if [[ -n "${child_pid:-}" ]]; then
    kill -TERM "$child_pid" 2>/dev/null || true
    wait "$child_pid" || true
  fi
  exit 0
}
trap term_handler SIGTERM SIGINT

# 3. FunciÃ³n de Espera (Wait-for-it)
# Usa 'nc' (netcat) para comprobar si un puerto estÃ¡ abierto y listo.
wait_for_host() {
  local host="$1"
  local port="$2"
  local timeout="$3"
  local start ts elapsed
  start=$(date +%s)
  echo "Esperando a $host:$port (timeout ${timeout}s)..."
  
  # Verificamos si 'nc' existe, si no, intentamos instalarlo (para imÃ¡genes minimalistas)
  if ! command -v nc &> /dev/null; then
    echo "Advertencia: Netcat (nc) no encontrado. Instalando..."
    if command -v apt-get &> /dev/null; then
      apt-get update && apt-get install -y netcat
    elif command -v apk &> /dev/null; then
      apk add netcat-openbsd
    else
      echo "ERROR: No se pudo instalar netcat. El script no podrÃ¡ esperar la DB. Abortando."
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

# 4. ExtracciÃ³n de Host/Puerto de la URL de la Base de Datos
if [ -z "$DB_HOST" ] && [ -n "$DATABASE_URL" ]; then
  # Extrae 'host:port' de postgres://user:pass@host:port/dbname
  host_port="$(echo "$DATABASE_URL" | awk -F@ '{print $2}' | awk -F/ '{print $1}')"
  DB_HOST="$(echo "$host_port" | cut -d: -f1)"
  DB_PORT="$(echo "$host_port" | cut -d: -f2)"
fi

# 5. Esperar a la Base de Datos (PostgreSQL por defecto)
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"

if ! wait_for_host "$DB_HOST" "$DB_PORT" "$WAIT_TIMEOUT"; then
  echo "ERROR: La base de datos $DB_HOST:$DB_PORT no respondiÃ³. Abortando."
  exit 1
fi

# 6. Esperar a Redis (Si REDIS_URL estÃ¡ definido)
if [ -n "$REDIS_URL" ]; then
  # Extrae 'host:port' de redis://host:port/db
  redis_host_port="$(echo "$REDIS_URL" | sed -E 's@^[^:]+://@@' | cut -d/ -f1)"
  REDIS_HOST="$(echo "$redis_host_port" | cut -d: -f1)"
  REDIS_PORT="$(echo "$redis_host_port" | cut -d: -f2)"
  
  REDIS_HOST="${REDIS_HOST:-redis}"
  REDIS_PORT="${REDIS_PORT:-6379}"
  
  # Redis es opcional, lo registramos como advertencia si falla el timeout
  if ! wait_for_host "$REDIS_HOST" "$REDIS_PORT" "$WAIT_TIMEOUT"; then
    echo "WARNING: Redis $REDIS_HOST:$REDIS_PORT no respondiÃ³ en ${WAIT_TIMEOUT}s. Continuando sin Redis."
  fi
fi

# 7. Ejecutar Migraciones (si la variable MIGRATE es true/1)
if [ "$MIGRATE" = "true" ] || [ "$MIGRATE" = "1" ]; then
  echo "Ejecutando migraciones..."
  python manage.py migrate --noinput
fi

# 8. Ejecutar Collectstatic (si la variable COLLECT_STATIC es true/1)
if [ "$COLLECT_STATIC" = "true" ] || [ "$COLLECT_STATIC" = "1" ]; then
  echo "Ejecutando collectstatic..."
  python manage.py collectstatic --noinput
fi

# 9. Iniciar el Comando Principal
# exec "$@" reemplaza el proceso del script shell con el comando que viene de Dockerfile/docker-compose.yml
echo "Iniciando proceso: $*"
exec "$@"
