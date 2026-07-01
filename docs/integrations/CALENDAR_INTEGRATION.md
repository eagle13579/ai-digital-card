# 日历集成指南

> AI数字名片 — Zoom + 腾讯会议日程/会议接入方案

---

## 1. 架构总览

```
┌─────────────────────────────┐
│   AI数字名片 后端            │
│  ┌───────────────────────┐  │
│  │  services/             │  │
│  │  ├── calendar_service │  │  ← 抽象基类 (CalendarBase)
│  │  ├── calendar_zoom    │  │  ← Zoom 实现
│  │  └── calendar_tencent │  │  ← 腾讯会议实现
│  │                       │  │
│  │  日历事件 → CRM 活动    │  │  ← 自动写入联系人时间线
│  └─────────┬─────────────┘  │
│            │ HTTP(S)        │
│            ▼                │
│    [Zoom API / 腾讯会议 API] │
└─────────────────────────────┘
```

所有日历集成继承 `CalendarBase`（`backend/app/services/calendar_service.py`），
提供统一的 `CalendarEvent` 数据模型和 `CalendarResult` 结果结构。

---

## 2. 功能矩阵

| 功能 | Zoom | 腾讯会议 |
|------|------|---------|
| 创建会议 | ✅ | ✅ |
| 列出会议 | ✅ | ✅ |
| 更新会议 | ✅ | ✅ |
| 删除会议 | ✅ | ✅ |
| 自动降级（无配置） | ✅ 日志输出 | ✅ 日志输出 |
| 鉴权方式 | Server-to-Server OAuth / JWT | JWT (HMAC-SHA256) |
| 关联 CRM 联系人 | ✅ contact_ids 参数 | ✅ contact_ids 参数 |
| 响应统一格式 | ✅ CalendarResult | ✅ CalendarResult |

---

## 3. 前置条件 (API 凭据)

### 3.1 Zoom

| 配置项 | 环境变量 | 说明 |
|--------|---------|------|
| Server-to-Server 账号 ID | `ZOOM_ACCOUNT_ID` | Zoom App Marketplace → Server-to-Server OAuth |
| Client ID | `ZOOM_CLIENT_ID` | Zoom App Credentials |
| Client Secret | `ZOOM_CLIENT_SECRET` | Zoom App Client Secret |
| API Key (JWT 方式) | `ZOOM_API_KEY` | 传统 JWT 方式（向后兼容） |
| API Secret (JWT 方式) | `ZOOM_API_SECRET` | 传统 JWT 方式（向后兼容） |

**推荐方式**: Server-to-Server OAuth（ZOOM_ACCOUNT_ID + ZOOM_CLIENT_ID + ZOOM_CLIENT_SECRET）。

**获取步骤：**
1. 登录 [Zoom App Marketplace](https://marketplace.zoom.us/)
2. 创建 App → 选择 "Server-to-Server OAuth"
3. 启用以下 Scopes:
   - `meeting:write:meeting` — 创建/更新/删除会议
   - `meeting:read:meeting` — 列出/读取会议
   - `user:read:user` — 读取用户信息（可选）
4. 复制 Account ID、Client ID、Client Secret 到 `.env`

### 3.2 腾讯会议

| 配置项 | 环境变量 | 说明 |
|--------|---------|------|
| App ID | `TENCENT_MEETING_APP_ID` | 腾讯会议开放平台应用 ID |
| SDK ID | `TENCENT_MEETING_SDK_ID` | SDK 标识（可选，默认同 App ID） |
| Secret | `TENCENT_MEETING_SECRET` | 应用签名密钥 |
| App ID（旧名） | `TENCENT_WECHAT_APP_ID` | 向后兼容 |
| Secret（旧名） | `TENCENT_WECHAT_SECRET` | 向后兼容 |

**获取步骤：**
1. 登录 [腾讯会议开放平台](https://open.meeting.tencent.com/)
2. 创建企业应用 → 获取 App ID 和 Secret
3. 在应用管理中配置回调 URL 和权限
4. 在 `.env` 中填入 `TENCENT_MEETING_APP_ID` 和 `TENCENT_MEETING_SECRET`

---

## 4. 配置（.env）

```env
# ── Zoom (推荐 Server-to-Server OAuth) ──────────────────────────────────────
# 全部缺失时自动降级为日志输出（无需配置即可正常运行）
ZOOM_ACCOUNT_ID=
ZOOM_CLIENT_ID=
ZOOM_CLIENT_SECRET=
# 或使用 JWT（向后兼容）
# ZOOM_API_KEY=
# ZOOM_API_SECRET=

# ── 腾讯会议 ────────────────────────────────────────────────────────────────
# 全部缺失时自动降级为日志输出（无需配置即可正常运行）
TENCENT_MEETING_APP_ID=
TENCENT_MEETING_SDK_ID=
TENCENT_MEETING_SECRET=
```

---

## 5. 快速集成

```python
from app.services.calendar_service import (
    CalendarEvent,
    CalendarResult,
    get_calendar,
    list_calendars,
)
from app.services.calendar_zoom import zoom_calendar
from app.services.calendar_tencent import tencent_calendar


# ── 使用 Zoom ─────────────────────────────────────────────────────────
# 自动检测: 有 ZOOM_* 环境变量 → 真实 API，无 → 存根（日志输出）

result = await zoom_calendar.create_event(
    user_id=123,
    title="产品演示 - 张三",
    start_time="2026-07-02T10:00:00",
    end_time="2026-07-02T11:00:00",
    description="演示AI数字名片新功能",
    contact_ids=[456, 789],  # 关联 CRM 联系人
)
if result.success and not result.degraded:
    print(f"Zoom 会议已创建: {result.event.meeting_url}")
elif result.degraded:
    print("Zoom 未配置，已在日志中记录会议信息")
else:
    print(f"创建失败: {result.error}")


# ── 使用腾讯会议 ──────────────────────────────────────────────────────

result = await tencent_calendar.create_event(
    user_id=123,
    title="客户需求沟通 - 李四",
    start_time="2026-07-02T14:00:00",
    end_time="2026-07-02T15:00:00",
    contact_ids=[456],
)
if result.success and not result.degraded:
    print(f"腾讯会议已创建: {result.event.meeting_url}")


# ── 列出会议 ─────────────────────────────────────────────────────────

# Zoom 会议列表
zoom_events = await zoom_calendar.list_events(user_id=123)
for event in zoom_events.events:
    print(f"[Zoom] {event.title} @ {event.start_time}")

# 腾讯会议列表
tencent_events = await tencent_calendar.list_events(user_id=123)
for event in tencent_events.events:
    print(f"[腾讯会议] {event.title} @ {event.start_time}")


# ── 更新会议 ─────────────────────────────────────────────────────────

await zoom_calendar.update_event(
    event_id="123456789",
    title="更新后的会议标题",
    start_time="2026-07-03T10:00:00",
)


# ── 删除会议 ─────────────────────────────────────────────────────────

await zoom_calendar.delete_event("123456789")


# ── 查看所有日历集成的启用状态 ──────────────────────────────────────

status = list_calendars()
# 输出: {"zoom": True, "tencent": False}
for platform, enabled in status.items():
    print(f"{platform}: {'✅ 已启用' if enabled else '⚠️ 未配置'}")
```

---

## 6. 数据模型

### CalendarEvent

平台无关的日程/会议统一数据模型：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `str` | 事件 ID（平台方唯一标识） |
| `title` | `str` | 事件标题 |
| `description` | `str` | 事件描述 |
| `start_time` | `str` | 开始时间（ISO 8601） |
| `end_time` | `str` | 结束时间（ISO 8601） |
| `timezone` | `str` | 时区（默认 Asia/Shanghai） |
| `location` | `str` | 地点/会议室 |
| `meeting_url` | `str` | 视频会议入会链接 |
| `meeting_id` | `str` | 会议号 |
| `meeting_password` | `str` | 会议密码 |
| `status` | `str` | 状态: scheduled/confirmed/cancelled/completed |
| `contact_ids` | `list[int]` | 关联的 CRM 联系人 ID 列表 |
| `owner_id` | `int` | 创建事件的用户 ID |
| `platform` | `str` | 来源平台: zoom/tencent |

### CalendarResult

所有日历操作的标准返回包装：

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | `bool` | 操作是否成功 |
| `degraded` | `bool` | 是否处于降级模式 |
| `event` | `CalendarEvent \| None` | 单个事件（创建/更新/查询） |
| `events` | `list[CalendarEvent]` | 事件列表（list） |
| `total` | `int` | 事件总数 |
| `error` | `str \| None` | 错误信息 |

---

## 7. 日历基类 API (CalendarBase)

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `list_events()` | user_id, start_time, end_time, page, page_size | `CalendarResult` | 列出日程事件 |
| `create_event()` | user_id, title, start_time, end_time, description, timezone, location, contact_ids | `CalendarResult` | 创建日程/会议 |
| `update_event()` | event_id, title, description, start_time, end_time, timezone, location, status | `CalendarResult` | 更新日程事件 |
| `delete_event()` | event_id | `CalendarResult` | 删除日程事件 |

所有方法均为降级安全:
- 平台未配置 → 记录日志，返回 `{success: True, degraded: True}`
- API 调用失败 → 记录错误日志，返回 `{success: False, error: "..."}`

---

## 8. 与 CRM 集成

日历事件通过 `contact_ids` 参数与 CRM 联系人关联：

```python
# 创建会议时关联联系人
result = await zoom_calendar.create_event(
    user_id=123,
    title="客户会议 - 张三",
    start_time="2026-07-02T10:00:00",
    end_time="2026-07-02T11:00:00",
    contact_ids=[456, 789],  # CRM 联系人 ID
)

# 后续可通过 CrmActivity 查询与某个联系人关联的会议活动
# (需要在 on_event_created 钩子中写入 CRM 活动记录)
```

`_on_event_created` 钩子可在子类中覆写，自动向 CRM 时间线写入活动记录：

```python
class MyZoomCalendar(ZoomCalendar):
    async def _on_event_created(
        self, event: CalendarEvent, result: CalendarResult
    ) -> None:
        # 写入 CRM 活动
        for contact_id in event.contact_ids:
            await crm_service.add_activity({
                "contact_id": contact_id,
                "activity_type": "meeting",
                "title": f"创建会议: {event.title}",
                "description": f"平台: {event.platform}\n时间: {event.start_time}\n入会链接: {event.meeting_url}",
                "source_model": "calendar_event",
                "source_record_id": event.id,
            })
```

---

## 9. 降级策略

| 场景 | 行为 |
|------|------|
| 平台凭据全缺 | 所有方法仅记录 `[平台名 降级]` 日志，返回 `degraded=True` |
| 平台凭据存在但无效 | API 调用返回 401，记录错误日志，返回 `success=False` |
| 平台凭据存在且有效 | 正常调用 API，返回 `success=True` |
| API 网络超时 | 捕获异常，记录错误日志，返回 `success=False` |

项目启动时自动在日志中输出启用状态：

```
INFO  Zoom 日历集成已启用 (server-to-server OAuth)
INFO  腾讯会议日历集成未配置 API 凭据 — 已降级到日志输出模式
```

建议使用 `list_calendars()` 在管理后台展示集成状态仪表盘。

---

## 10. 错误处理

```python
from app.services.calendar_service import CalendarResult

result = await zoom_calendar.create_event(...)
if not result.success:
    logger.error("[日历] Zoom 创建会议失败: %s", result.error)
    # 触发告警 / 重试队列
elif result.degraded:
    logger.warning("[日历] Zoom 未配置，会议已记录到日志")
else:
    logger.info("[日历] 会议创建成功: %s", result.event.meeting_url)
```

---

## 11. 安全注意事项

- **永不提交** 含真实 Token/Secret 的 .env 文件到 Git
- 使用 GitHub Secrets / Vault 管理生产凭据
- Zoom Server-to-Server OAuth Token 有效期为 1 小时，SDK 自动处理刷新
- 腾讯会议 JWT 有效期为 24 小时，每次请求重新生成
- 日历事件中的 `meeting_password` 为敏感信息，日志输出时注意脱敏

---

## 12. 生产替换清单

- [x] `pip install httpx PyJWT` (已在依赖中)
- [x] 创建 `calendar_service.py` — 日历基类 + 数据模型 + 注册表
- [x] 创建 `calendar_zoom.py` — Zoom 集成（S2S OAuth / JWT）
- [x] 创建 `calendar_tencent.py` — 腾讯会议集成（JWT 签名）
- [x] 配置 `.env.example` 中的日历凭据模板
- [x] 创建本文档 `CALENDAR_INTEGRATION.md`
- [x] 在 `__init__.py` 中导出新服务
- [ ] 补充集成测试 (`tests/calendar/test_calendar.py`)
- [ ] 实现 CRM 活动自动记录（`_on_event_created` 钩子）
- [ ] 在 CI/CD 中执行集成测试
- [ ] 添加日历事件列表 API 路由
