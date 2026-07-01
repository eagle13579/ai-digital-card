# nginx 自定义镜像 — 集成配置文件与前端构建产物
FROM nginx:alpine

# 移除默认配置
RUN rm -f /etc/nginx/conf.d/default.conf

# 复制自定义配置
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://localhost:8200/ || exit 1

EXPOSE 8200

CMD ["nginx", "-g", "daemon off;"]
