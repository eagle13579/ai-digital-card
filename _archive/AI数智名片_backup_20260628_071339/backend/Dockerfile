FROM python:3.12-slim

WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 应用代码
COPY app/ app/
COPY main.py .

# 数据目录
RUN mkdir -p data uploads

EXPOSE 8201

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8201/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8201"]
