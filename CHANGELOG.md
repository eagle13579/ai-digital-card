# Changelog

## [v2.2.0] — 2026-06-05
### 工业化全量交付 (2.7/10 → 7.0/10)

#### Added
- 三层架构: models/services/routers/middleware 完全分离
- Docker容器化: multi-stage build + docker-compose + HEALTHCHECK
- CI/CD: GitHub Actions (lint→test→build→deploy)
- i18n: 中英双语支持 (zh.json + en.json)
- Sentry可观测性集成
- pytest测试框架 (8文件, 2922行, 覆盖核心API+中间件+模型+匹配引擎+信任网络)
- API版本重定向中间件 (/api/v1/xxx → /xxx)
- 生产级Docker配置 (资源限制+日志+健康检查)

#### Changed
- 密码哈希: SHA256+固定盐 → bcrypt+随机盐
- 数据库: 支持 DATABASE_URL 环境变量切换 PostgreSQL
- RateLimit: 标准headers (RateLimit-Limit/Remaining/Reset)

#### Infrastructure
- requirements.txt + .env + .gitignore + config.py
- deploy.sh 一键部署脚本
- Makefile 统一管理
- Git版本管理 (tag: v2.2.0)

## [v2.1] — 2026-05-30
### 产品化里程碑
- 3Tab SPA界面
- 企业信任网络四层模型
- 智能匹配引擎
- 计名设计哲学注入
- 12预置用户

## [v2.0] — 2026-05-28
### 前端升级
- 3Tab界面 (编辑/画册/匹配)
- 企业信任网络
- 匹配引擎算法

## [v1.0] — 2026-05-27
### 初始版本
- 基础画册CRUD
- 二维码生成
- FastAPI单体架构
