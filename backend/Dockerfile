FROM python:3.12-slim

WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 项目代码
COPY . .

# 非root用户
RUN useradd -m -u 1000 app && chown -R app:app /app
USER app

EXPOSE 8201

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8201"]
