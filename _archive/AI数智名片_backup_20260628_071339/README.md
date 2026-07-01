# AI数智名片

> AI驱动的数字化名片 + 智能画册平台

## 三层架构

```
D:\AI数智名片\                  ← Layer 1: 工程代码
└── backend/                      FastAPI 后端 (端口 8201)
    ├── main.py                   入口文件
    ├── app/
    │   ├── routers/              路由层
    │   ├── services/             服务层
    │   ├── ai/                   AI 引擎（OCR + NLP + 向量搜索）
    │   ├── models/               数据模型
    │   ├── middleware/           中间件
    │   └── templates/            HTML 模板
    ├── tests/                    测试
    └── requirements.txt          依赖

D:\向海容的知识库\...\产品开发\AI数智名片\  ← Layer 2: 产品资产
    ├── ARCHITECTURE.md           架构设计
    ├── PRD-index.md              产品需求索引
    └── GATEWAY.md                链客宝网关设计

D:\向海容的知识库\...\profiles\ai-digital-card\  ← Layer 3: 工作环境
    └── README.md                 工作环境说明
```

## 快速开始

```bash
# 安装依赖
cd backend
pip install -r requirements.txt

# 配置 .env
cp .env.example .env
# 编辑 .env 填入 DeepSeek API Key

# 启动
python main.py
# → http://localhost:8201
```

## 端口说明

| 端口 | 服务 | 说明 |
|:----:|:-----|:------|
| 8200 | Nginx | 统一接入层（生产） |
| 8201 | FastAPI | 后端 API |
| 8202 | Brochure | 画册微服务（规划） |

## 核心能力

- 📇 **名片 OCR** — 扫描纸质名片自动结构化
- 🤖 **AI 提取** — DeepSeek NLP 提取 + 摘要 + 智能排版
- 📖 **智能画册** — 多页翻页画册（3D StPageFlip）
- 🔗 **供需匹配** — 三层评分匹配引擎
- 🔐 **信任网络** — 社交关系评分
- 🌐 **国际化** — 中英文双语支持

## 技术栈

| 层 | 技术 |
|:---|:------|
| 后端 | FastAPI + SQLAlchemy + SQLite |
| AI | PaddleOCR + DeepSeek API + M3E Embedding |
| 前端 | HTML Templates / PWA |
| 部署 | Nginx + Docker |
