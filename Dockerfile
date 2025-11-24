# ---------- Build stage ----------
FROM python:3.11-slim-bookworm AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libpq5 \
      netcat-openbsd \
      graphviz \
      libgraphviz-dev \
      pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

COPY requirements.txt .

ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt

# ---------- Final stage ----------
FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libpq5 \
      netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV

RUN groupadd -r appgroup \
  && useradd -r -g appgroup -m -d /home/appuser -s /sbin/nologin appuser \
  && mkdir -p /usr/src/app

WORKDIR /usr/src/app

# Copiar entrypoint desde la raíz del contexto de build
COPY entrypoint.sh /usr/src/app/entrypoint.sh
RUN chmod +x /usr/src/app/entrypoint.sh

# Copiar el resto del código
COPY --chown=appuser:appgroup . .

RUN chown -R appuser:appgroup $VIRTUAL_ENV /usr/src/app

EXPOSE 8000

USER appuser

ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
CMD ["gunicorn", "feria_conectada.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--log-level", "info"]