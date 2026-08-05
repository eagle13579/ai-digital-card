# notification — 行业动态推送模块

基于 [follow-builders](https://github.com/nousresearch/follow-builders) 的 `multi_channel_delivery` 模块，
为 AI 数字名片提供统一的多渠道推送能力。

## 架构

```
backend/notification/
├── __init__.py               # 模块入口，导出 UnifiedPushService
├── notification_service.py   # 统一推送服务（三种模式 + 三种渠道）
├── config.yaml               # 推送渠道和模式路由配置
└── README.md                 # 本文档
```

## 依赖

- `baize_libs/multi_channel_delivery` — 发送后端（StdoutDelivery, TelegramDelivery, EmailDelivery）
- `PyYAML` — 配置解析（已包含在项目依赖中或 `pip install pyyaml`）

`baize_libs` 位于 `D:\向海容的知识库\wiki\wiki\记忆宫殿\profiles\evolution\_shared_sync\baize_libs\`
运行时自动加入 `sys.path`，无需手动配置。

## 三种推送模式

| 模式 | 枚举 | 触发时机 | 适用场景 |
|------|------|----------|----------|
| 实时推送 | `PushMode.REALTIME` | API 请求时即时发送 | 新匹配、新消息、新访客 |
| 定时推送 | `PushMode.SCHEDULED` | 每日定时任务 | 每日摘要、动态汇总 |
| 主动拉取 | `PushMode.PULL` | 用户查看名片时 | 名片被查看通知、互动提醒 |

## 三种推送渠道

| 渠道 | 类 | 配置 method | 所需凭证 |
|------|----|-------------|----------|
| 标准输出 | `StdoutDelivery` | `stdout` | 无 |
| Telegram | `TelegramDelivery` | `telegram` | `TELEGRAM_BOT_TOKEN` 环境变量 + `chatId` |
| 邮件 | `EmailDelivery` | `email` | `RESEND_API_KEY` 环境变量 + `to` / `from` |

## 快速开始

```python
from notification.notification_service import UnifiedPushService

svc = UnifiedPushService()

# 实时推送
svc.push_realtime("🎯 新匹配: 张三 × 李四")

# 定时摘要
svc.push_scheduled("今日新增 12 个匹配，3 条新消息")

# 主动拉取
svc.push_pull("user_42", "李四查看了您的名片")
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/notification/push` | 手动触发行业动态推送（支持指定模式和渠道） |

请求体示例:
```json
{
  "mode": "realtime",
  "text": "🎉 新匹配通知",
  "subject": "实时动态",
  "channels": ["stdout"]
}
```

## 配置

编辑 `config.yaml` 控制:
- 哪些渠道启用（`stdout` / `telegram` / `email`）
- 每种模式使用哪些渠道

环境变量（Telegram / Email 所需）:
- `TELEGRAM_BOT_TOKEN` — Telegram Bot Token
- `RESEND_API_KEY` — Resend API Key
