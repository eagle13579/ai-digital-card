# ── Stage 1: Build / Install ───────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies needed for some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ── Stage 2: Runtime ──────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY app/ app/
COPY scripts/ scripts/

# Ensure local binaries (uvicorn, etc.) are in PATH
ENV PATH=/root/.local/bin:$PATH

# Expose the application port
EXPOSE 8003

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003", "--workers", "2"]
