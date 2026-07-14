# =============================================================================
# AI数智名片 — Backend Docker Image (Python 3.12 Slim)
# =============================================================================
# 构建: docker build -t ai-digital-card-backend -f Dockerfile .
# 运行: docker run -d -p 8201:8201 --env-file .env ai-digital-card-backend
# =============================================================================

FROM python:3.12-slim

LABEL maintainer="AI数智名片团队"
LABEL description="AI数智名片 Backend API — Docker 容器化"
LABEL version="1.0.0"

# ── 系统依赖 ────────────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ── Python 依赖 ────────────────────────────────────────────────────────────
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# ── 项目代码 ───────────────────────────────────────────────────────────────
# 只复制 app/ 目录和根级文件 (main.py 等)，排除 venv、__pycache__ 等
COPY app/ ./app/
COPY main.py .
COPY _cron_process_queue.py .

# ── 必要目录 ───────────────────────────────────────────────────────────────
RUN mkdir -p /app/data /app/logs /app/uploads && \
    find /app -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true

# ── 非 root 用户 ──────────────────────────────────────────────────────────
RUN addgroup --system --gid 1001 app && \
    adduser --system --uid 1001 --gid 1001 --no-create-home app && \
    chown -R app:app /app
USER app

# ── 环境变量 ───────────────────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ── 暴露端口 ───────────────────────────────────────────────────────────────
EXPOSE 8201

# ── 健康检查 ───────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; exit(0 if urllib.request.urlopen('http://127.0.0.1:8201/health').status == 200 else 1)"

# ── 启动命令 ───────────────────────────────────────────────────────────────
# main.py 在 WORKDIR /app 根目录下，from app import create_app → app = create_app()
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8201", "--log-level", "info"]
