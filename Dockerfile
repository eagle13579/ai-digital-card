# ============================================================
# Stage 1: Build — Python dependencies + virtual environment
# ============================================================
FROM python:3.12-slim AS build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install build system dependencies
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        gcc \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies (from backend/)
COPY backend/requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ============================================================
# Stage 2: Runtime — minimal image with non‑root user
# ============================================================
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_PORT=8201

WORKDIR /app

# Install runtime essentials only (curl for healthcheck)
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from build stage
COPY --from=build /opt/venv /opt/venv

# Copy application code (backend/ subtree only)
COPY backend/ .

# Create non‑root user and own /app
RUN groupadd -r appuser && \
    useradd -r -g appuser -d /app -s /sbin/nologin appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE ${APP_PORT}

# Health check — hits /health every 30s
HEALTHCHECK --interval=30s --timeout=5s \
    CMD curl -f http://localhost:${APP_PORT}/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8201"]
