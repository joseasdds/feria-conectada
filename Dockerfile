# ----------------------------------------------------------------------
# Build Stage: instalar dependencias y construir un virtualenv
# ----------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS builder

# Instalar dependencias del sistema necesarias para compilar paquetes nativos
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libpq5 \
      netcat-openbsd \
      # Dependencias de Graphviz para graph_models
      graphviz \
      libgraphviz-dev \
      pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo para la build
WORKDIR /usr/src/app

# Copiar sólo requirements para aprovechar la cache de docker
COPY requirements.txt .

# Crear y activar virtualenv
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Actualizar pip e instalar dependencias (sin cache)
RUN pip install --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt

# ----------------------------------------------------------------------
# Final Stage: imagen runtime ligera (Bindeando en 0.0.0.0:8000)
# ----------------------------------------------------------------------
FROM python:3.11-slim-bookworm

# Variables de entorno recomendadas para Django en contenedores
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Instalar dependencias de runtime mínimas
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libpq5 \
      netcat-openbsd \
    # Limpiar el cache de apt-get para reducir el tamaño final de la imagen
    && rm -rf /var/lib/apt/lists/*

# Copiar virtualenv desde la etapa builder
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV

# Crear un usuario sin privilegios para ejecutar la app (mejor seguridad)
RUN groupadd -r appgroup \
  && useradd -r -g appgroup -m -d /home/appuser -s /sbin/nologin appuser \
  && mkdir -p /usr/src/app

# Establecer directorio de trabajo
WORKDIR /usr/src/app

# Copiar entrypoint y dar permisos de ejecución
COPY entrypoint.sh /usr/src/app/entrypoint.sh
RUN chmod +x /usr/src/app/entrypoint.sh # <--- LÍNEA AÑADIDA PARA PERMISOS DE EJECUCIÓN

# Copiar el código de la aplicación
COPY --chown=appuser:appgroup . .

# Asegurarse de que el virtualenv y el código pertenezcan al usuario no-root
RUN chown -R appuser:appgroup $VIRTUAL_ENV /usr/src/app

# Exponer puerto de la aplicación (solo informativo)
EXPOSE 8000

# Ejecutar como usuario no-root
USER appuser

# ENTRYPOINT: el script debe encargarse de cosas como wait-for-db, migrate, collectstatic (si aplica)
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]

# CMD: arrancar gunicorn en 0.0.0.0:8000
CMD ["gunicorn", "feria_conectada.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--log-level", "info"]