# 订阅运营文档

> AI 数字名片 — 订阅系统运营手册
> 最后更新: 2026-07-01

---

## 目录

1. [套餐概览](#1-套餐概览)
2. [试用到期流程](#2-试用到期流程)
3. [取消/退款策略](#3-取消退款策略)
4. [续费提醒](#4-续费提醒)
5. [API 参考](#5-api-参考)
6. [运营常见问题](#6-运营常见问题)

---

## 1. 套餐概览

| 套餐 | 价格 | 试用 | 特点 |
|------|------|------|------|
| **免费版** | ¥0/月 | — | 基础名片、30天访客记录 |
| **标准版** | ¥99/月 | 14天免费试用 | 智能匹配、无限访客、API |
| **企业版** | ¥499/月 | 14天免费试用 | SSO、自定义域名、团队协作 |

套餐等级权重: `free(0) → standard(1) → enterprise(2)`

**升级路径**: free → standard → enterprise (仅支持单向顺序升级)
**降级路径**: enterprise → standard → free (仅支持单向顺序降级)

---

## 2. 试用到期流程

### 2.1 试用周期

- 试用时长: **14天** (配置: `TRIAL_DAYS = 14`, `subscription_service.py`)
- 试用套餐: **标准版** (配置: `TRIAL_TIER = "standard"`)
- 每个用户 **仅限一次** 免费试用

### 2.2 到期提醒时间节点

系统自动在以下时间节点检查并发送试用到期通知:

| 时间节点 | 触发条件 | 提醒内容 |
|----------|----------|----------|
| **提前 3 天** | `days_remaining == 3` | 📅 还有 3 天到期 |
| **提前 1 天** | `days_remaining == 1` | ⏰ 明天到期 |
| **到期当天** | `days_remaining == 0` | ⚠️ 今天到期 |

配置: `NOTIFY_BEFORE_DAYS = [3, 1, 0]` (`subscription_notifier.py`)

### 2.3 检查机制

**服务文件**: `backend/app/services/subscription_notifier.py`

```python
# 核心函数
async def check_and_notify(db: AsyncSession, days_before: int | None = None) -> dict
```

- `days_before=None`: 检查所有配置的时间节点 (3天/1天/当天)
- `days_before=3`: 仅检查 3 天后到期的试用
- 返回所有需要通知的提醒记录列表

### 2.4 手动触发检查

**API**: `POST /api/subscription/notify/check`

- 权限: 仅 `admin` / `superadmin`
- 使用场景: 后台运营人员手动触发
- 返回: 所有已生成并发送的通知列表

**cURL 示例**:
```bash
curl -X POST "https://api.example.com/api/subscription/notify/check" \
  -H "Authorization: Bearer <admin_token>"
```

### 2.5 通知通道（当前实现）

当前阶段，通知仅输出到**日志**，格式如下:

```
[TrialNotify] user_id=123 sub_id=45 days_left=3 type=trial_expiring msg=📅 试用即将到期...
```

**预留通道** (待接入):
- 站内消息 (Message 模型)
- 短信 (短信网关)
- 邮件 (邮件服务)
- App 推送 (推送服务)

### 2.6 试用到期后行为

| 到期后状态 | 用户操作 |
|------------|----------|
| 试用到期 → 未升级 | 自动降级为免费版（需手动在 `cancel_at_period_end` 侧处理或定时任务） |
| 试用到期 → 已升级 | 转为正式标准版/企业版 |
| 试用中途取消 | 标记为 `expired`，停止服务 |

> **注意**: 当前试用到期后系统不会自动降级用户权限。运营建议搭配定时任务（如每日执行一次 `/notify/check`）或在用户登录时检查试用状态。

---

## 3. 取消/退款策略

### 3.1 两种取消模式

#### 模式 A: 周期末取消 (`POST /api/subscription/cancel`)

| 属性 | 说明 |
|------|------|
| **操作** | 设置 `auto_renew = False` |
| **服务状态** | 保持活跃至当前计费周期结束 |
| **退款** | 无退款 |
| **适用场景** | 用户不再续费，但想用完已付费周期 |
| **到期后** | 自动降级为免费版 |

#### 模式 B: 立即取消 + 退款 (`POST /api/subscription/cancel-immediate`)

| 属性 | 说明 |
|------|------|
| **操作** | 状态设为 `cancelled`，立即终止服务 |
| **退款** | 按比例计算退款 |
| **用户权限** | 立即降级为 `free` |
| **适用场景** | 用户不满意，要求立即退款 |

### 3.2 退款计算公式

```
已用天数 = max(1, cancel_date - start_date)
总天数   = max(1, end_date - start_date)
退款比例 = 1 - (已用天数 / 总天数)
退款金额 = floor(总金额 × 退款比例)    # 向下取整到分
```

**重要规则**:
- 试用订阅退款金额为 **¥0** (未实际付费)
- 退款金额最小为 ¥0（不退负数）
- 退款向下取整到分（`int()` 截断）
- 如果取消时间在订阅周期外，不产生退款

### 3.3 退款示例

| 场景 | 总金额 | 已用天数 | 总天数 | 退款金额 |
|------|--------|----------|--------|----------|
| 第1天取消标准版 | ¥99 | 1 | 30 | ¥95 (96.6%) |
| 第15天取消标准版 | ¥99 | 15 | 30 | ¥49 (50%) |
| 第29天取消标准版 | ¥99 | 29 | 30 | ¥3 (3.3%) |
| 试用期取消 | ¥0 | 7 | 14 | ¥0 |

### 3.4 取消原因枚举

前端通过 `GET /api/subscription/cancel/reasons` 获取原因下拉列表:

| 枚举值 | 中文标签 |
|--------|----------|
| `too_expensive` | 价格太高 |
| `not_using` | 使用频率低 / 不常用 |
| `missing_features` | 缺少需要的功能 |
| `switching_alternative` | 切换到其他替代产品 |
| `temporary_pause` | 暂时不需要，后续再续费 |
| `quality_issues` | 产品质量问题 |
| `bugs_or_errors` | 遇到错误或 Bug |
| `customer_service` | 客服体验不佳 |
| `other` | 其他原因 |

### 3.5 退款实际资金处理

> **注意**: 当前退款计算仅做**逻辑记录**，实际的资金退还（原路返回/提现等）需要对接支付渠道的退款 API。

建议对接流程:
1. `cancel_immediate()` 记录应退金额到 `features.refund_info`
2. 异步任务/Webhook 调用支付网关退款接口
3. 退款成功后更新数据库状态

---

## 4. 续费提醒

### 4.1 续费逻辑

- 付费订阅默认 `auto_renew = True`
- 升级时自动设置自动续费
- 周期末取消时设置 `auto_renew = False`

### 4.2 续费提醒建议

当前系统暂未实现自动续费提醒，建议后续完善:

| 时间节点 | 提醒内容 | 方式 |
|----------|----------|------|
| 到期前 7 天 | 您的订阅即将到期，请确保账户余额充足 | 邮件/站内信 |
| 到期前 3 天 | 您的订阅还有 3 天到期 | 邮件/短信 |
| 到期前 1 天 | 您的订阅明天到期 | 短信/推送 |
| 续费失败 | 续费失败，请更新支付方式 | 短信/App推送 |
| 续费成功 | 续费成功，下一周期至 YYYY-MM-DD | 邮件/站内信 |

### 4.3 续费失败处理

当 `auto_renew = True` 但续费失败时:
1. 保留当前服务（宽限期 3 天）
2. 每天发送续费失败提醒
3. 宽限期结束后降级为免费版

---

## 5. API 参考

### 5.1 订阅查询

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/subscription/plans` | 套餐列表与定价 |
| GET | `/api/subscription/current` | 当前订阅信息 |
| GET | `/api/subscription/trial/status` | 试用状态查询 |

### 5.2 订阅操作

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/subscription/upgrade` | 升级套餐 |
| POST | `/api/subscription/downgrade` | 降级套餐 |
| POST | `/api/subscription/trial/start` | 开通 14 天试用 |

### 5.3 到期通知

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| POST | `/api/subscription/notify/check` | admin | 手动触发试用到期检查 |

### 5.4 取消/退款

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/subscription/cancel/reasons` | 取消原因列表 |
| POST | `/api/subscription/cancel` | 周期末取消 |
| POST | `/api/subscription/cancel-immediate` | 立即取消 + 退款 |

---

## 6. 运营常见问题

### Q1: 用户试用过期后还能使用服务吗？

目前试用过期后系统不会自动降级。建议:
- 运营后台定期执行 `/notify/check` 查看试用到期列表
- 后续可在用户登录时检查试用状态，提示升级
- 或添加定时任务自动处理过期试用

### Q2: 退款多久到账？

当前退款仅在系统中记录金额。实际到账时间取决于对接的支付渠道:
- 微信支付: 1-3 个工作日原路返回
- 支付宝: 即时到账（部分银行卡 1-3 天）

### Q3: 用户取消后还能恢复吗？

- 周期末取消: 在 end_date 之前，管理员可在后台修改 `auto_renew` 恢复
- 立即取消: 数据保留，用户可重新购买订阅

### Q4: 如何查看取消统计？

取消原因记录在 `EnterpriseSubscription.features` JSON 字段中，可通过数据库查询:
```sql
SELECT features->>'cancel_reason' AS reason, COUNT(*) AS cnt
FROM enterprise_subscriptions
WHERE features->>'cancelled_at' IS NOT NULL
GROUP BY reason;
```

### Q5: 支持按比例退款到部分天数吗？

支持。公式已实现按天比例退款。特殊场景（如使用不满 24 小时全额退款）可通过 `reason_detail` 字段人工处理。

---

## 附录: 服务文件结构

```
backend/app/services/
├── subscription_service.py    # 订阅核心逻辑: 套餐定义、试用、升级/降级
├── subscription_notifier.py   # 试用到期通知服务 (本文第2节)
└── subscription_cancel.py     # 自助取消/退款服务 (本文第3节)

backend/app/routers/
└── subscription_router.py     # 订阅 API 路由 (含新增通知+取消端点)

docs/ops/
└── SUBSCRIPTION_OPS.md        # 本文档
```
