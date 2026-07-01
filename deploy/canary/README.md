# 金丝雀发布 (Canary Release)

> AI数字名片 — 渐进式发布配置说明

---

## 概述

金丝雀发布（Canary Release）是一种渐进式部署策略，先给一小部分流量（金丝雀实例）部署新版本，
通过监控指标判断版本健康度后，逐步放大流量直至全量发布，异常时自动回滚。

**已有基础：**
- `.github/workflows/canary.yml` — Kubernetes 版金丝雀 CI/CD 工作流
- `deploy/canary.yml` — 金丝雀发布配置（权重/时长/指标阈值）
- `deploy/canary/` — 金丝雀 Nginx 配置模板

---

## 目录结构

```
deploy/canary/
├── README.md            ← 本文件
└── nginx-canary.conf    ← 金丝雀 Nginx 路由模板
```

---

## 发布流程

```
                    ┌──────────────┐
                    │  构建镜像     │
                    │  (canary tag) │
                    └──────┬───────┘
                           ▼
                   ┌───────────────┐
                   │ 部署 Canary   │
                   │ weight=10%    │ ◄── 首批 10% 流量
                   └───────┬───────┘
                           ▼
                  ┌────────────────┐
                  │ 监控 30 分钟    │
                  │ error < 1%     │
                  │ p99  < 3s      │
                  └───────┬────────┘
                     ╱         ╲
                    ▼           ▼
            ┌──────────┐   ┌──────────┐
            │ 放大 50%  │   │ 自动回滚 │
            │ 监控 1h   │   │ (Revert) │
            └─────┬────┘   └──────────┘
                  ▼
            ┌──────────┐
            │ 全量 100% │
            │ 完成发布  │
            └──────────┘
```

---

## Nginx 流量分流

`nginx-canary.conf` 通过 `split_clients` 模块实现按用户 client_id / IP 的百分比分流：

```nginx
split_clients "${remote_addr}${http_user_agent}" $canary_backend {
    10%    backend_canary;   # 金丝雀后端
    *      backend_stable;   # 稳定版后端
}
```

金丝雀版本与稳定版本共用同一个 Nginx 实例，金丝雀比例可在运行时通过变量调整。

---

## 指标判定

| 阶段 | 错误率阈值 | P99 延迟阈值 | 观察窗口 |
|------|-----------|-------------|---------|
| canary (10%) | < 1% | < 3s | 30 分钟 |
| staging (50%) | < 0.5% | < 2s | 1 小时 |
| production (100%) | — | — | 永久 |

回滚触发条件: **错误率 > 2% 持续 5 分钟** → 自动切回 stable 版本。

---

## 快速开始

### 手动触发金丝雀发布

```bash
# CI 手动触发 (GitHub Actions)
# 1. 进入 Actions → Canary Release → Run workflow
# 2. 输入镜像 tag（或留空使用 git sha）
# 3. 设定监控时长和错误率阈值

# 或直接使用 deploy/canary.yml
cp deploy/canary.yml deploy/canary.yml.active
# 修改配置后执行 CI 触发
```

### 本地 Nginx 调试

```bash
# 启动金丝雀 Nginx
docker run -d --name canary-nginx \
  -p 8200:8200 \
  -v $(pwd)/deploy/canary/nginx-canary.conf:/etc/nginx/conf.d/default.conf:ro \
  nginx:alpine
```

### 验证分流

```bash
# 多次请求查看 X-Canary 响应头
for i in $(seq 1 100); do
  curl -sI http://localhost:8200/api/health | grep -i x-canary
done
```

---

## 配置模板说明

| 文件 | 用途 |
|------|------|
| `deploy/canary/README.md` | 本文档 |
| `deploy/canary/nginx-canary.conf` | Nginx 金丝雀分流配置 |
| `deploy/canary.yml` | 金丝雀参数配置权重/时长/阈值 |
| `.github/workflows/canary.yml` | CI/CD 自动化工作流 |

---

## 故障排除

| 问题 | 排查步骤 |
|------|---------|
| 分流比例不准 | 检查 `split_clients` hash key 是否包含了足够变量 |
| 金丝雀实例无流量 | 确认 `nginx-canary.conf` 已挂载到 Nginx |
| 自动回滚未触发 | 检查健康检查端的 `/metrics` 是否正常暴露 |
| Pod 启动失败 | 检查 K8s liveness/readiness probe 配置 |

---

## 参考

- [deploy/canary.yml](../canary.yml) — 金丝雀参数配置
- [.github/workflows/canary.yml](../../.github/workflows/canary.yml) — CI/CD 工作流
- [deploy/nginx.conf](../nginx.conf) — 生产 Nginx 配置
- [deploy/blue_green_deploy.sh](../blue_green_deploy.sh) — 蓝绿部署脚本（备选策略）
