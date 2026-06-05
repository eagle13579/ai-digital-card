# 变更日志

## [2.2.0] — 2026-06-02 — 工业化全量升级

### 新增
- 🏗️ **CI/CD 流水线** — GitHub Actions: push触发→pytest测试→前端构建→SSH部署
- 🔐 **bcrypt 密码加密** — SHA256+固定盐 → bcrypt，旧密码登录时自动升级
- 🗄️ **Alembic 数据库迁移** — 版本化管理7张表Schema变更
- 🧪 **pytest 测试框架** — 38个测试覆盖认证/画册CRUD/匹配引擎核心路径
- 🐳 **Docker 容器化** — Dockerfile + docker-compose.yml 一键部署
- 📋 **依赖锁定** — requirements.txt + .gitignore

### 变更
- `digital_brochure_api.py`: 密码哈希从SHA256升级为bcrypt，新增`_verify_password`函数，`db_authenticate_user`登录时自动检测旧密码并升级
- 修复 `TOKEN_EXPIRE_HOURS=***` 占位符bug → 改为 `=72`
- 新增 `HASH_SALT_OLD` 常量用于旧密码兼容

### 技术债补齐
- 依赖从硬编码变为锁定管理
- 密码安全从自建哈希升级为工业标准bcrypt
- 数据库从 `CREATE TABLE IF NOT EXISTS` 升级为Alembic版本化迁移
- 部署从手动SSH升级为CI/CD自动流水线

---

## [2.1.0] — 2026-05-31 — 产品功能完成

### 新增
- 3Tab SPA 主应用（我的画册/电子画册/智能匹配）
- 信任网络四层模型
- 多维匹配引擎（需求匹配40% + 信任价值30% + 标签20% + 认证加分10%）
- 翻页图册（StPageFlip 3D翻页效果）
- 画册编辑器（6步创建向导）
- 访客感知与二维码生成
- 链客宝桥接模块

### 设计注入
- 计名4原则：3秒法则 · 减法设计 · 场景适配 · 价值先行

---

## [2.0.0] — 2026-05-30 — 架构重构

### 新增
- FastAPI v2.2 重写后端
- SQLite WAL模式 + 外键约束
- Bearer Token 认证系统
- 统一响应格式 `{code, data, message}`

### 变更
- 从Flask迁移到FastAPI
- 从单文件HTML重构为前后端分离

---

## [1.0.0] — 2026-05-25 — MVP

- 初始版本
- Flask + SQLite 基础架构
- 画册CRUD + 简单匹配
