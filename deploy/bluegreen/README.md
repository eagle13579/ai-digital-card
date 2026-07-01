# AI数智名片 — 蓝绿部署一键启用指南

> 零宕机部署：蓝色(8201) 生产 / 绿色(8202) 新版本，通过 Nginx 无感知切换。

---

## 目录

- [架构概览](#架构概览)
- [前置条件](#前置条件)
- [三步启用](#三步启用)
  - [第 1 步：配置 Nginx](#第-1-步配置-nginx)
  - [第 2 步：加载配置](#第-2-步加载配置)
  - [第 3 步：验证部署](#第-3-步验证部署)
- [执行切换](#执行切换)
- [回滚操作](#回滚操作)
- [一键验证](#一键验证)
- [故障排查](#故障排查)
- [文件清单](#文件清单)

---

## 架构概览

```
                      ┌──────────────┐
                      │  用户请求      │
                      └──────┬───────┘
                             │
                      ┌──────▼───────┐
                      │  Nginx :8200  │ ← 流量网关
                      │  (bluegreen)  │
                      └──┬────────┬──┘
                         │        │
              ┌──────────▼──┐  ┌──▼──────────┐
              │ 蓝色(Blue)   │  │ 绿色(Green)  │
              │ 后端 :8201  │  │ 后端 :8202  │
              │ (当前生产)   │  │ (新版本备用)  │
              └─────────────┘  └─────────────┘
```

| 组件 | 端口 | 用途 |
|------|------|------|
| Nginx 网关 | **8200** | 统一入口，根据 active_backend 路由流量 |
| 蓝色后端 | **8201** | 当前生产环境 (默认) |
| 绿色后端 | **8202** | 新版本备用环境 (切换目标) |

切换原理：Nginx `map` 指令决定流量去向，修改 `default` 值并重载即可无感切换。

---

## 前置条件

| 依赖 | 要求 | 检查命令 |
|------|------|----------|
| Nginx | ≥1.18 | `nginx -v` |
| curl | 任意版本 | `curl --version` |
| 后端服务 | 端口 8201 健康 | `curl http://127.0.0.1:8201/health` |
| 项目路径 | `D:/AI数智名片` | — |

> **Windows 用户注意**：本指南使用 Linux 路径语法 (`/etc/nginx/...`)。
> Windows 上 Nginx 配置通常位于 `C:\nginx\conf\` 或安装目录下的 `conf\` 文件夹，请相应调整路径。

---

## 三步启用

### 第 1 步：配置 Nginx

将蓝绿部署配置复制到 Nginx 配置目录：

```bash
# Linux / macOS
sudo cp deploy/bluegreen/nginx-bluegreen.conf /etc/nginx/conf.d/bluegreen.conf

# Windows (PowerShell, 以 C:\nginx 为例)
copy D:\AI数智名片\deploy\bluegreen\nginx-bluegreen.conf C:\nginx\conf\conf.d\bluegreen.conf
```

或者创建符号链接以便于更新：

```bash
sudo ln -sf $(pwd)/deploy/bluegreen/nginx-bluegreen.conf /etc/nginx/conf.d/bluegreen.conf
```

### 第 2 步：加载配置

```bash
# 检查语法
sudo nginx -t

# 若无报错，重载配置（零宕机）
sudo nginx -s reload
```

成功应输出：

```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### 第 3 步：验证部署

```bash
# 一键验证（推荐）
bash deploy/bluegreen/verify.sh

# 或手动检查
curl http://127.0.0.1:8200/health/blue   # 应返回蓝色后端健康
curl http://127.0.0.1:8200/health/green  # 备用环境同样可查
```

访问 `http://localhost:8200/api/` 确认应用正常。

---

## 执行切换

### 🔄 切换到绿色（新版本上线）

```bash
bash deploy/bluegreen/switch-green.sh
```

该脚本会：

1. ✅ 检查绿色环境健康（端口 8202）
2. 🔀 修改 Nginx `active_backend` 为 `backend_green`
3. 🔄 重载 Nginx 使变更生效
4. ✅ 验证切换结果

### 🔵 切回蓝色（回滚旧版本）

```bash
bash deploy/bluegreen/switch-blue.sh
```

---

## 回滚操作

### 方式 A：一键切换脚本（推荐）

```bash
bash deploy/bluegreen/switch-blue.sh
```

### 方式 B：手动回滚

```bash
# 1. 修改 Nginx 配置指向蓝色
sudo sed -i 's/default backend_green;/default backend_blue;/' /etc/nginx/conf.d/bluegreen.conf

# 2. 验证并重载
sudo nginx -t && sudo nginx -s reload
```

### 方式 C：从备份恢复

切换脚本会自动备份配置到 `deploy/rollback/` 目录：

```bash
# 查看可用备份
ls deploy/rollback/bluegreen.conf.bak.*

# 恢复最近备份
sudo cp deploy/rollback/bluegreen.conf.bak.$(ls -t deploy/rollback/ | head -1) /etc/nginx/conf.d/bluegreen.conf
sudo nginx -t && sudo nginx -s reload
```

### 方式 D：清理绿色容器

回滚后可以安全移除绿色环境：

```bash
docker rm -f ai-digital-card-green 2>/dev/null || true
```

---

## 一键验证

使用 `verify.sh` 脚本进行全面检查：

```bash
# 完整验证（端口 + Nginx + 配置语法 + 模拟切换）
bash deploy/bluegreen/verify.sh

# 快速检查（仅端口 + 状态摘要）
bash deploy/bluegreen/verify.sh --quick
```

检查项：

| 检查项 | 说明 |
|--------|------|
| 端口 8201 | 蓝色后端是否监听 |
| 端口 8202 | 绿色后端是否监听 |
| 端口 8200 | Nginx 网关是否监听 |
| HTTP /health | 后端健康端点是否可访问 |
| Nginx 命令 | nginx 是否安装且在 PATH |
| 配置语法 | `nginx -t` 语法检查 |
| 切换脚本 | switch-blue/switch-green 是否存在且可执行 |
| 配置部署状态 | 蓝绿配置是否已部署到 Nginx |
| 活跃环境 | 当前流量指向蓝色还是绿色 |
| 模拟切换 | dry-run 展示完整切换流程 |

---

## 故障排查

### ❌ `nginx: command not found`

```bash
# Linux
sudo apt install nginx      # Debian/Ubuntu
sudo yum install nginx      # CentOS/RHEL

# Windows
# 下载: https://nginx.org/en/download.html
# 解压到 C:\nginx\，并将 C:\nginx\ 加入 PATH

# macOS
brew install nginx
```

### ❌ 端口被占用

```bash
# 查看 8200 端口占用
netstat -ano | grep 8200
```

如需修改端口，编辑 `nginx-bluegreen.conf` 中的 `listen` 指令。

### ❌ 后端服务未启动

```bash
# 启动蓝色后端
docker-compose up -d backend

# 检查日志
docker logs ai-digital-card-blue --tail 50
```

### ❌ Nginx 配置语法错误

检查 `nginx-bluegreen.conf` 中引用的路径（日志目录、SSL 证书等）是否存在，不存在则创建或修改路径：

```bash
# 创建日志目录
sudo mkdir -p /var/log/nginx/
sudo touch /var/log/nginx/ai-digital-card-access.log
sudo touch /var/log/nginx/ai-digital-card-error.log
```

### ❌ 切换后 API 无响应

```bash
# 确认后端已启动
curl http://127.0.0.1:8202/health

# 检查 Nginx 错误日志
tail -50 /var/log/nginx/ai-digital-card-error.log

# 检查 Nginx 当前配置
grep 'default ' /etc/nginx/conf.d/bluegreen.conf
```

---

## 文件清单

```
deploy/bluegreen/
├── nginx-bluegreen.conf     # Nginx 蓝绿路由配置（上游 + 安全头 + 健康端点）
├── switch-blue.sh           # 切换脚本 → 蓝色环境 8201
├── switch-green.sh          # 切换脚本 → 绿色环境 8202
├── health_check.sh          # 健康检查工具（支持 --port / --all / --wait）
├── verify.sh                # 一键验证脚本（端口 + 配置 + 模拟切换）
└── README.md                # ← 本文档
```

---

> **提示**：建议在首次部署前运行 `bash deploy/bluegreen/verify.sh` 确认环境就绪，
> 部署新版本前再次运行确认蓝色环境稳定。
