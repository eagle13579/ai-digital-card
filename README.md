# AI数字名片 (Digital Business Card)

> 链接链客宝企业家生态圈的智能电子名片系统

## 产品定位

一分钟创建个人/企业数字画册，通过名片匹配+标签推荐实现精准商业连接。
企业家的「移动商务厅」。

## 核心功能

- **3Tab SPA**: ①我的画册(编辑) ②电子画册(预览/分享) ③智能匹配
- **企业信任网络**: 四层模型(身份认证→信任价值→信任连接→信任证据)
- **智能匹配引擎**: 需求匹配40% + 信任价值30% + 标签20% + 认证10%
- **认证标识**: 金牌/已认证/未认证三级体系

## 技术栈

| 层级 | 技术 |
|:-----|:------|
| 后端 | FastAPI + SQLite + Uvicorn |
| 前端 | Alpine.js + Tailwind CSS (SPA) |
| 认证 | Bearer Token + bcrypt |
| 中间件 | 限流 / 请求ID / 指标 / i18n |
| 部署 | Docker + GitHub Actions CI |

## 快速启动

```bash
# 1. 克隆并安装依赖
cd backend
pip install -r requirements.txt

# 2. 启动服务
python main.py
# → http://localhost:8003

# 3. 或Docker启动
docker-compose up -d
```

## API文档

- `http://localhost:8003/docs` — Swagger UI
- `http://localhost:8003/redoc` — ReDoc

## 环境变量

| 变量 | 默认值 | 说明 |
|:-----|:-------|:------|
| PORT | 8003 | 服务端口 |
| DB_PATH | data/digital_brochure.db | SQLite路径 |
| SECRET_KEY | (必填) | JWT/Token密钥 |
| SENTRY_DSN | (可选) | Sentry DSN |
| LOG_LEVEL | INFO | 日志级别 |

## 项目结构

```
AI数字名片/
├── backend/
│   ├── app/
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务逻辑
│   │   ├── routers/        # API路由
│   │   ├── middleware/     # 中间件
│   │   ├── templates/      # 前端模板
│   │   └── static/         # 静态资源
│   ├── tests/              # 测试
│   └── main.py             # 入口
├── digital_brochure_api.py # (旧单体,建议迁移到backend/)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 设计哲学

计名4原则: 3秒法则 · 减法设计 · 场景适配 · 价值先行

---
*AI数字名片 v2.1 — 链客宝生态产品*
