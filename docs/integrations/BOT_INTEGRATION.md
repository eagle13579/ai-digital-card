# Bot 集成文档

> AI数字名片 — 即时通讯机器人接入方案
> 适用平台: Slack / 飞书 / 钉钉

---

## 1. 架构总览

```
┌────────────┐    Webhook/WebSocket    ┌──────────────────┐
│  IM 平台   │ ◄────────────────────►  │  AI数字名片 Bot  │
│ (Slack/    │                        │  Service          │
│  飞书/钉钉) │    Event Callback      │  ┌────────────┐  │
│            │ ◄────────────────────  │  │ handlers/   │  │
│            │                        │  │ ├── slack/  │  │
│            │    Message Reply       │  │ ├── feishu/ │  │
│            │  ────────────────────► │  │ ├── dingtalk│  │
└────────────┘                        │  │ └── common/ │  │
                                      │  └────────────┘  │
                                      └──────────────────┘
```

Bot 服务独立部署（或作为 FastAPI 子应用），通过 Webhook/WebSocket 接收消息，
处理后调用后端 API 返回名片数据、搜索、交换等能力。

---

## 2. 功能矩阵

| 功能 | Slack | 飞书 | 钉钉 |
|------|-------|------|------|
| 搜索名片 | ✅ | ✅ | ✅ |
| 名片分享 | ✅ | ✅ | ✅ |
| 名片交换 | ✅ | ✅ | ✅ |
| 查看自己名片 | ✅ | ✅ | ✅ |
| 查看交互记录 | ✅ | ✅ | ✅ |
| 群内@机器人回复 | ✅ | ✅ | ✅ |
| 私聊机器人 | ✅ | ✅ | ✅ |
| 消息卡片 (Rich) | ✅ Block Kit | ✅ 消息卡片 | ✅ 互动卡片 |
| OAuth 登录绑定 | ✅ | ✅ | ✅ |
| 企业自建应用 | ❌ (需 Slack App) | ✅ | ✅ |
| 企业市场应用 | ✅ | ✅ | ✅ |

---

## 3. 各平台接入方案

### 3.1 Slack

#### 前置条件

| 项目 | 说明 |
|------|------|
| App 类型 | Slack App (可发布到 Slack App Directory) |
| 技术方案 | Socket Mode (WebSocket) 或 HTTP Events API |
| 推荐方式 | Socket Mode（无需公网暴露） |
| 交互组件 | Block Kit (Slack 消息卡片) |

#### 配置项

```env
SLACK_BOT_TOKEN=xoxb-xxx-xxx-xxx
SLACK_SIGNING_SECRET=xxx
SLACK_APP_TOKEN=xapp-xxx-xxx-xxx  # Socket Mode 专用
SLACK_SOCKET_MODE=true            # true=Socket Mode, false=HTTP
```

#### 关键 Scope

```
bot: chat:write, channels:history, groups:history, im:history, users:read
```

#### 核心命令

| 命令 | 描述 |
|------|------|
| `/card search <name>` | 搜索名片 |
| `/card me` | 查看我的名片 |
| `/card share <email>` | 分享名片给指定用户 |
| `/card exchange @user` | 发起名片交换 |
| `/card help` | 查看帮助 |

#### 参考 SDK

```python
# pip install slack-sdk slack-bolt
from slack_bolt import App

app = App(token=os.getenv("SLACK_BOT_TOKEN"), signing_secret=os.getenv("SLACK_SIGNING_SECRET"))
```

#### 事件处理存根

创建 `backend/app/services/bot/handlers/slack_handler.py`:

```python
# 示例: Slack 消息处理入口
@app.event("app_mention")
def handle_mention(event, say):
    text = event["text"]
    if "搜索" in text:
        # 调用名片搜索 API
        say(f"找到以下名片: ...")
    elif "我的名片" in text:
        # 查询当前用户名片
        say("你的数字名片: ...")
```

---

### 3.2 飞书 (Lark / Feishu)

#### 前置条件

| 项目 | 说明 |
|------|------|
| 应用类型 | 企业自建应用 / 商店应用 |
| 技术方案 | HTTP Webhook + 飞书开放 API |
| 推荐方式 | Event Callback + Card Action |
| 交互组件 | 飞书消息卡片 (Card Kit) |

#### 配置项

```env
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx
FEISHU_VERIFICATION_TOKEN=xxx
FEISHU_ENCRYPT_KEY=xxx
FEISHU_BOT_NAME=AI数字名片
```

#### 关键权限

```
contact:user.base:readonly, im:message, im:resource, im:chat
```

#### 核心事件

| Event Type | 描述 |
|------------|------|
| `im.message.receive_v1` | 接收消息（私聊 + 群@） |
| `card.action.trigger` | 消息卡片交互回调 |
| `event_callback` | URL 验证 + 基础事件 |

#### 参考 SDK

```python
# pip install lark-oapi
from lark_oapi import Client, Config

client = Client(Config(
    app_id=os.getenv("FEISHU_APP_ID"),
    app_secret=os.getenv("FEISHU_APP_SECRET"),
))
```

#### 命令示例

| 命令 | 描述 |
|------|------|
| `搜索 张三` | 搜索名片 |
| `我的名片` | 查看个人名片 |
| `分享 张三 -> user@company.com` | 分享名片 |
| `交换` | 发起名片交换 |

---

### 3.3 钉钉 (DingTalk)

#### 前置条件

| 项目 | 说明 |
|------|------|
| 应用类型 | 企业内应用 / 第三方企业应用 |
| 技术方案 | HTTP Webhook + 钉钉开放 API |
| 推荐方式 | Event Callback + 互动卡片 |
| 交互组件 | 钉钉互动卡片 (Card JSON) |

#### 配置项

```env
DINGTALK_APP_KEY=xxx
DINGTALK_APP_SECRET=xxx
DINGTALK_AGENT_ID=xxx
DINGTALK_CARD_TEMPLATE_ID=xxx
```

#### 关键权限

```
qyapi_imchat_write, qyapi_contact_read, qyapi_robot_send
```

#### 核心事件

| Event Type | 描述 |
|------------|------|
| `event_callback.check_url` | URL 验证回调 |
| `event_callback.robot_text` | 机器人文本消息 |
| `card_callback` | 互动卡片回调 |

#### 参考 SDK

```python
# pip install dingtalk-sdk
from dingtalk import DingTalkClient

client = DingTalkClient(os.getenv("DINGTALK_APP_KEY"), os.getenv("DINGTALK_APP_SECRET"))
```

#### 命令示例

| 命令 | 描述 |
|------|------|
| `搜索 张三` | 搜索名片 |
| `我的名片` | 查看个人名片 |
| `分享 user@company.com` | 分享名片 |
| `帮助` | 查看帮助 |

---

## 4. Bot 服务部署

### 4.1 目录结构

```
backend/app/services/bot/
├── __init__.py
├── bot_service.py          # Bot 注册与路由入口
├── config.py               # 各平台配置加载
├── handlers/
│   ├── __init__.py
│   ├── common.py           # 跨平台公共逻辑
│   ├── slack_handler.py    # Slack 事件处理
│   ├── feishu_handler.py   # 飞书事件处理
│   └── dingtalk_handler.py # 钉钉事件处理
├── models.py               # 消息模型
└── utils.py                # 工具函数
```

### 4.2 Webhook 路由注册

在 `backend/app/routers/bot_router.py` 中注册：

```python
from fastapi import APIRouter, Request

router = APIRouter(prefix="/bot", tags=["bot"])

@router.post("/slack/events")
async def slack_events(request: Request):
    from app.services.bot.handlers.slack_handler import handler
    return await handler.handle(request)

@router.post("/feishu/webhook")
async def feishu_webhook(request: Request):
    from app.services.bot.handlers.feishu_handler import handle_event
    return await handle_event(request)

@router.post("/dingtalk/webhook")
async def dingtalk_webhook(request: Request):
    from app.services.bot.handlers.dingtalk_handler import handle_event
    return await handle_event(request)
```

### 4.3 消息处理流程

```
收到消息 → 平台识别 → 命令解析 → 权限校验
                             ↓
                      ┌─── 搜索名片 → 调用搜索 API → 返回卡片
                      │─── 我的名片 → 查询用户 → 返回卡片
                      │─── 分享名片 → 验证目标 → 发送分享
                      │─── 名片交换 → 生成交换请求 → 通知双方
                      └─── 其他 → 返回帮助文本
```

---

## 5. 消息卡片模板

各平台卡片 JSON 模板存放于 `backend/app/services/bot/templates/`：

```
backend/app/services/bot/templates/
├── slack/
│   ├── card_search.json        # 搜索结果卡片
│   ├── card_profile.json       # 个人名片卡片
│   └── card_exchange.json      # 交换请求卡片
├── feishu/
│   ├── card_search.json
│   ├── card_profile.json
│   └── card_exchange.json
└── dingtalk/
    ├── card_search.json
    ├── card_profile.json
    └── card_exchange.json
```

---

## 6. 安全与限流

- **请求签名验证**: 所有 Webhook 入口必须验证平台签名（Slack Signing Secret / 飞书 Verification Token / 钉钉签名）
- **频率限制**: 每用户每分钟最多 20 条 Bot 交互请求
- **权限隔离**: 用户只能搜索/操作自己有权限的名片（通过 OAuth 绑定的用户身份鉴权）
- **敏感信息**: 名片卡片中不展示手机号等敏感信息，需点击「查看详情」跳转至 App

---

## 7. 测试与调试

```bash
# 单元测试
pytest backend/tests/test_bot/ -v

# 本地调试 Slack Socket Mode
SLACK_SOCKET_MODE=true python -m backend.app.services.bot.slack_dev

# 本地调试飞书/钉钉 (需 ngrok 暴露公网 webhook)
ngrok http 8201
```

---

## 8. 平台对比总结

| 维度 | Slack | 飞书 | 钉钉 |
|------|-------|------|------|
| 开发成本 | ★★☆ (中等) | ★★★ (较复杂) | ★★☆ (中等) |
| 文档质量 | ★★★★★ | ★★★☆☆ | ★★★☆☆ |
| SDK 成熟度 | ★★★★★ | ★★★★☆ | ★★★☆☆ |
| 企业市场覆盖 | 海外为主 | 国内中大型 | 国内全量 |
| 消息卡片灵活性 | 高 (Block Kit) | 中 (Card Kit) | 中 (互动卡片) |
| Socket Mode | ✅ | ❌ (仅 HTTP) | ❌ (仅 HTTP) |
| 推荐优先级 | 1 (海外优先) | 2 (国内一线城市) | 3 (国内全覆盖) |

---

> **下一步**: 从推荐优先级最高的平台开始实现，按 `backend/app/services/bot/` 目录结构创建存根 handler，完成 Webhook 注册后逐步替换为真实 SDK 调用。
