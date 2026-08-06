# AI数智名片 — 工作环境

## 三层路径

| 层 | 路径 | 说明 |
|:---|:-----|:------|
| Layer 1 工程代码 | `D:\AI数智名片\` | 后端 + 前端 + 部署 |
| Layer 2 产品资产 | `D:\向海容的知识库\wiki\wiki\记忆宫殿\L5孵化室\产品开发\AI数智名片\` | 文档 + 设计 |
| Layer 3 工作环境 | `D:\向海容的知识库\wiki\wiki\记忆宫殿\profiles\ai-digital-card\` | 当前文件 |

## 快速启动

```bash
# 1. 安装后端依赖
cd D:\AI数智名片\backend
pip install -r requirements.txt

# 2. 启动后端
python main.py
# → 后端运行在 http://localhost:8201

# 3. 访问前端
# 打开 http://localhost:8201/
```

## 端口映射

| 服务 | 端口 | 说明 |
|:-----|:----:|:------|
| Nginx 接入层 | 8200 | 统一入口 |
| FastAPI 后端 | 8201 | API 服务 |
| Brochure 服务 | 8202 | 画册微服务（规划） |

## 代码收割源

本项目从以下项目收割代码：
- **AI数字名片** (`D:\向海容的知识库\wiki\wiki\记忆宫殿\L5孵化室\产品开发\AI数字名片\`) — 核心后端代码
- **链客宝** (`D:\向海容的知识库\wiki\wiki\记忆宫殿\L5孵化室\产品开发\链客宝\`) — 会员体系 + 支付（待收割）

## 关键文档

- `ARCHITECTURE.md` — 架构设计
- `PRD-index.md` — 产品需求索引
- `GATEWAY.md` — 链客宝网关设计
