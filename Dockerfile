# =============================================================================
# Dockerfile — AI数字名片 (Digital Brochure API)
# Multi-stage build: python:3.11-slim
# =============================================================================

# ── Stage 1: Base ────────────────────────────────────────────────────────────
FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files & enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# ── Stage 2: Install dependencies ───────────────────────────────────────────
FROM base AS builder

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Stage 3: Runtime ────────────────────────────────────────────────────────
FROM builder AS runtime

# Install curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Ensure the backend package is importable
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Expose the application port
EXPOSE 8003

# Health check (curl-based, more reliable and lightweight than python-urllib)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Start the API server
CMD ["uvicorn", "digital_brochure_api:app", "--host", "0.0.0.0", "--port", "8003"]
