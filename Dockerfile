# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Prevent .pyc files and enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Poetry configuration — install into the system Python, no virtualenv needed inside Docker
ENV POETRY_VERSION=1.8.3 \
    POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR /app

# ── System dependencies ────────────────────────────────────────────────────────
# curl: used by the official Poetry installer
# libpq-dev + gcc: required to build/link psycopg2
# nginx: reverse proxy that converts HEAD → GET for health-check monitors
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        libpq-dev \
        gcc \
        nginx \
    && rm -rf /var/lib/apt/lists/* \
    # Remove the default site so only our config is active.
    && rm -f /etc/nginx/sites-enabled/default \
    # Drop the 'user' directive so nginx runs as whoever launched the container.
    && sed -i '/^user /d' /etc/nginx/nginx.conf

# ── Install Poetry ─────────────────────────────────────────────────────────────
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

# ── Install Python dependencies (pip / requirements.txt) ──────────────────────
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ── Install project dependencies via Poetry ────────────────────────────────────
# Copy only the dependency manifests first so Docker can cache this layer
# independently from the rest of the source code.
COPY pyproject.toml poetry.lock ./
RUN poetry install --without dev --no-root

# ── nginx reverse-proxy config ────────────────────────────────────────────────
COPY nginx/steelworks.conf /etc/nginx/conf.d/steelworks.conf

# ── Container startup script ──────────────────────────────────────────────────
COPY start.sh ./
RUN chmod +x start.sh

# ── Copy application source ────────────────────────────────────────────────────
COPY . .

# Create directories for data and logs if they don't already exist
RUN mkdir -p data/production_logs data/quality_logs data/shipping_logs logs

# Streamlit listens on 8501 by default
EXPOSE 8501

# Streamlit listens on 8502 (loopback only); nginx proxies 8501 → 8502.
ENV STREAMLIT_SERVER_ADDRESS=127.0.0.1 \
    STREAMLIT_SERVER_PORT=8502 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Database connection — override at runtime with -e DATABASE_URL=...
ENV DATABASE_URL=postgresql://postgres:password@db:5432/steelworks_ops

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"

ENTRYPOINT ["./start.sh"]
