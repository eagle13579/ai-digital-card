# AI数智名片 — 架构文档

> 这是 AI 数字名片的**唯一核心代码库**。  
> 其他冗余目录和旧副本已归档到 `_archive/`。

---

## 目录结构

```
D:\AI数智名片\
├── _archive/               ← 已归档的旧副本（备份、小程序、WebComponent、App）
├── backend/                ← FastAPI 后端 API 服务（378 文件）
│   ├── main.py             入口文件 (uvicorn, port 8201)
│   ├── app/
│   │   ├── routers/        路由层
│   │   ├── models/         数据模型
│   │   ├── services/       服务层
│   │   ├── middleware/     中间件
│   │   ├── ai/             AI 引擎（OCR + NLP + 向量搜索）
│   │   └── payment/        支付模块
│   ├── tests/              测试
│   └── requirements.txt    依赖
├── frontend/               ← React 19 + Vite 6 前端（7745 文件）
│   ├── index.html          HTML 入口
│   ├── vite.config.ts      Vite 配置（代理 /api → :8201）
│   ├── package.json        依赖（React 19, Vite 6, Tailwind CSS v4）
│   ├── src/                源码
│   ├── dist/               构建输出
│   └── nginx_html/         Nginx 静态资源
├── deploy/                 ← 部署配置（22 文件）
├── docs/                   文档
├── k8s/                    Kubernetes 编排
├── k6/                     性能测试
├── e2e/                    E2E 测试
├── scripts/                工具脚本
├── data/                   数据
├── tests/                  集成测试
├── training_data/          训练数据
├── backups/                备份
├── .github/                GitHub Actions CI
├── docker-compose.yml      Docker Compose 编排
├── Dockerfile              Docker 构建
├── Makefile                构建命令
└── ARCHITECTURE.md         ← 本文档
```

---

## 端口与服务

| 端口 | 服务 | 说明 |
|:----:|:-----|:------|
| 8201 | FastAPI | 后端 API（开发/生产） |
| 5173 | Vite Dev Server | 前端开发服务器 |
| 8200 | Nginx | 统一接入层（生产） |

---

## 后端架构 (FastAPI :8201)

- **框架**: FastAPI + SQLAlchemy + SQLite
- **入口**: `backend/main.py` → `app.create_app()`
- **路由**: `app/routers/` 按功能模块划分
- **AI 引擎**: `app/ai/` — PaddleOCR + DeepSeek API + M3E Embedding
- **中间件**: `app/middleware/` — CORS, 鉴权, 日志

## 前端架构 (React 19 + Vite 6 :5173)

- **框架**: React 19 + TypeScript
- **构建**: Vite 6（proxy /api → localhost:8201）
- **样式**: Tailwind CSS v4 + motion（动画）
- **路由**: react-router-dom v7
- **图标**: lucide-react
- **PWA**: 支持 Service Worker + manifest.json

---

## 已归档内容 (`_archive/`)

以下目录已移入 `_archive/`，不再作为开发目标：

| 存档目录 | 原用途 |
|:---------|:--------|
| `_archive/AI数智名片_backup_20260628_071339/` | 旧完整备份 |
| `_archive/AI数字名片App/` | 移动端 App（已合并） |
| `_archive/AI数字名片WebComponent/` | Web Component 实现（已合并） |
| `_archive/AI数字名片小程序/` | 微信小程序（已合并） |
