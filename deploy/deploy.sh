#!/bin/bash
# AI数字名片 一键部署脚本
# 用法: ssh root@47.116.116.87 'bash -s' < deploy.sh

set -e
APP_DIR="/var/www/ai-digital-card"
echo "🚀 AI数字名片 一键部署"

# 1. 拉取最新代码
cd "$APP_DIR" || { echo "❌ 目录不存在, 先clone"; git clone git@github.com:eagle13579/ai-digital-card.git "$APP_DIR"; cd "$APP_DIR"; }
git pull origin master
echo "✅ 代码已更新"

# 2. 配置Docker镜像加速
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://docker.xuanyuan.me"
  ],
  "log-driver": "json-file",
  "log-opts": {"max-size": "10m", "max-file": "3"}
}
EOF
systemctl restart docker 2>/dev/null || true
sleep 3

# 3. 拉取基础镜像
docker pull docker.1ms.run/library/python:3.12-slim
docker tag docker.1ms.run/library/python:3.12-slim python:3.12-slim 2>/dev/null || true
docker pull docker.1ms.run/node:20-alpine
docker tag docker.1ms.run/node:20-alpine node:20-alpine 2>/dev/null || true
echo "✅ 基础镜像已就绪"

# 4. 构建并启动
docker compose build backend --progress=plain 2>&1 | tail -5
docker compose build frontend --progress=plain 2>&1 | tail -5
docker compose up -d
echo "✅ 服务已启动"

# 5. 健康检查
sleep 10
curl -sf http://localhost:8201/health && echo "✅ 后端健康" || echo "⚠️ 后端健康检查失败"
curl -sf http://localhost:3000 && echo "✅ 前端在线" || echo "⚠️ 前端检查失败"

# 6. 配置Nginx (从deploy/bluegreen复制)
if [ -f deploy/bluegreen/nginx-bluegreen.conf ]; then
  cp deploy/bluegreen/nginx-bluegreen.conf /etc/nginx/sites-available/ai-digital-card.conf
  ln -sf /etc/nginx/sites-available/ai-digital-card.conf /etc/nginx/sites-enabled/
  nginx -t && systemctl reload nginx
  echo "✅ Nginx配置已加载"
fi

echo ""
echo "🎉 AI数字名片部署完成"
echo "   https://your-domain.com → 前端"
echo "   https://your-domain.com/api → 后端"
