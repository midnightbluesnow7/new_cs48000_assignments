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
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        libpq-dev \
        gcc \
    && rm -rf /var/lib/apt/lists/*

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

# ── Copy application source ────────────────────────────────────────────────────
COPY . .

# Create directories for data and logs if they don't already exist
RUN mkdir -p data/production_logs data/quality_logs data/shipping_logs logs

# Streamlit listens on 8501 by default
EXPOSE 8501

# Override Streamlit defaults so the app is reachable inside Docker
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Database connection — override at runtime with -e DATABASE_URL=...
ENV DATABASE_URL=postgresql://postgres:password@db:5432/steelworks_ops

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"

ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
