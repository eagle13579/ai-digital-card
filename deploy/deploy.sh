#!/bin/bash
# AI数智名片 部署脚本
# 用法: ./deploy.sh [backend|frontend|all]

set -e

PROJECT_ROOT="/var/www/ai-digital-card"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
NGINX_CONF="$PROJECT_ROOT/deploy/nginx.conf"

echo "===== AI数智名片 部署脚本 ====="

deploy_backend() {
    echo "[1/3] 部署后端..."
    cd "$BACKEND_DIR"
    
    # 安装依赖
    pip install -r requirements.txt --quiet
    
    # 创建数据目录
    mkdir -p data uploads
    
    # 重启后端服务
    if systemctl is-active --quiet ai-digital-card-backend; then
        systemctl restart ai-digital-card-backend
    else
        echo "  → 后端服务未注册 systemd，请手动启动:"
        echo "    cd $BACKEND_DIR && python main.py &"
    fi
    
    echo "[1/3] 后端部署完成"
}

deploy_frontend() {
    echo "[2/3] 部署前端..."
    cd "$FRONTEND_DIR"
    
    if [ -f "package.json" ]; then
        npm install --quiet
        npm run build
    else
        echo "  → 前端项目不存在，跳过"
    fi
    
    echo "[2/3] 前端部署完成"
}

deploy_nginx() {
    echo "[3/3] 部署 Nginx 配置..."
    if [ -f "$NGINX_CONF" ]; then
        cp "$NGINX_CONF" /etc/nginx/conf.d/ai-digital-card.conf
        nginx -t && systemctl reload nginx
        echo "[3/3] Nginx 配置已更新"
    else
        echo "  → Nginx 配置文件不存在，跳过"
    fi
}

case "${1:-all}" in
    backend)
        deploy_backend
        ;;
    frontend)
        deploy_frontend
        ;;
    all)
        deploy_backend
        deploy_frontend
        deploy_nginx
        echo "===== 部署完成 ====="
        echo "后端: http://localhost:8201"
        echo "前端: http://localhost:8200"
        ;;
    *)
        echo "用法: $0 [backend|frontend|all]"
        exit 1
        ;;
esac
