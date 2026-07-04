# 链客宝 — 定价引擎 + 用量计费系统

## 概览

定价引擎(Pricing Engine) + 用量追踪(Usage Tracker) 是链客宝商业化的核心基础设施，提供：

- **三级定价体系**: Free (免费) / Pro (¥99/月) / Enterprise (¥499/月)
- **多种计费模式**: 月付、年付、按量计费、附加包
- **用量追踪**: 按用户+按月汇总各功能使用量
- **配额控制**: 基于定价层的功能配额自动限流
- **智能折扣**: 年付折扣、首月优惠、优惠券、推荐奖励
- **阈值告警**: 用量达 80% 时自动触发通知

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Pricing Engine                          │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ 报价计算     │  │ 配额检查     │  │ 折扣引擎         │   │
│  │ (calculate)  │  │ (check_quota)│  │ (coupon/first/   │   │
│  │              │  │              │  │  referral)       │   │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘   │
│         │                 │                    │             │
│  ┌──────┴─────────────────┴────────────────────┴────────┐   │
│  │              YAML 配置 (config/pricing.yaml)          │   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Usage Tracker                           │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ 用量记录     │  │ 月度汇总     │  │ 阈值告警         │   │
│  │ (record)     │  │ (monthly)    │  │ (80% threshold)  │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
│                       │                                     │
│              ┌────────┴────────┐                            │
│              │ monthly_usage   │ (SQLAlchemy ORM)           │
│              │ usage_alert_logs│                            │
│              └─────────────────┘                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      API 路由                                │
│  GET  /api/v1/pricing/plans                                 │
│  GET  /api/v1/pricing/usage                                 │
│  POST /api/v1/pricing/quote                                 │
│  POST /api/v1/pricing/upgrade                               │
│  GET  /api/v1/pricing/invoice                               │
└─────────────────────────────────────────────────────────────┘
```

## 配置

### pricing.yaml

定价配置位于 `backend/config/pricing.yaml`，包含：

| 章节 | 说明 |
|------|------|
| `tiers` | 定价层定义 (free/pro/enterprise) 含价格和功能配额 |
| `addons` | 附加包 (额外名片/匹配/存储/AI聊天) |
| `coupons` | 优惠券 (fixed/percentage) |
| `first_month_discount` | 首月优惠活动配置 |
| `referral_reward` | 推荐奖励配置 |
| `tax_rate` | 增值税率 (默认6%) |
| `yearly_discount_rate` | 年付折扣率 (默认16.67%) |

### 修改配置

1. 编辑 `backend/config/pricing.yaml`
2. 调用 `POST /api/v1/pricing/reload` 热加载 (无需重启)
3. 或用 Python: `PricingEngine().reload()`

## 服务组件

### PricingEngine (`app/services/pricing_engine.py`)

单例模式定价引擎，核心方法：

| 方法 | 说明 |
|------|------|
| `list_plans()` | 返回所有定价层 |
| `get_plan(tier)` | 获取单个定价层详情 |
| `calculate_quote(...)` | 报价计算 |
| `check_quota(tier, key, used, add)` | 配额检查 |
| `validate_upgrade(current, new)` | 升级/降级验证 |
| `reload()` | 热加载配置 |

#### calculate_quote 参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| tier_id | str | — | free/pro/enterprise |
| billing_cycle | str | monthly | monthly/yearly |
| seats | int | 1 | 座位数 |
| coupon_code | str | "" | 优惠券码 |
| is_first_month | bool | False | 首月优惠 |
| is_referral | bool | False | 推荐奖励 |
| addon_ids | list | [] | 附加包ID列表 |

### UsageTracker (`app/services/usage_tracker.py`)

用量追踪器，核心方法：

| 方法 | 说明 |
|------|------|
| `record_usage(user_id, key, units)` | 记录用量增加 |
| `batch_record(user_id, {key: units})` | 批量记录 |
| `get_usage(user_id, key)` | 查询单项用量 |
| `get_usage_summary(user_id, tier)` | 获取完整用量摘要 |
| `get_usage_history(user_id, key, months)` | 历史趋势 |
| `check_thresholds(user_id, tier)` | 阈值检测 |

#### 追踪的用量键

| 键 | 说明 | 单位 |
|------|------|------|
| api_calls | API 调用次数 | 次 |
| business_cards_created | 名片创建数 | 张 |
| matches_performed | 匹配次数 | 次 |
| ai_chat_sessions | AI 聊天次数 | 次 |
| storage_bytes | 存储空间 | 字节 |

### 数据库表

| 表 | 说明 |
|------|------|
| `monthly_usage` | 按月汇总的用户用量 |
| `usage_alert_logs` | 用量告警日志 (去重) |

## API 端点

### 定价方案

```
GET  /api/v1/pricing/plans
GET  /api/v1/pricing/plans/{tier}
GET  /api/v1/pricing/addons
GET  /api/v1/pricing/coupon/{code}
GET  /api/v1/pricing/config
GET  /api/v1/pricing/first-month-discount
GET  /api/v1/pricing/referral-reward
```

### 报价

```
POST /api/v1/pricing/quote
```

请求体:
```json
{
  "tier": "pro",
  "billing_cycle": "yearly",
  "seats": 1,
  "coupon_code": "CHAINKEWELCOME",
  "is_first_month": false,
  "is_referral": false,
  "addon_ids": ["additional_matches"]
}
```

响应:
```json
{
  "tier": "pro",
  "billing_cycle": "yearly",
  "total": 871.27,
  "total_cny": "¥871.27",
  "breakdown": [
    {"label": "单价 (yearly)", "amount": 990.0},
    {"label": "座位数 × 1", "amount": 990.0},
    {"label": "年付折扣 (17%)", "amount": -165.03},
    {"label": "优惠券", "amount": -50.0},
    {"label": "增值税 6%", "amount": 49.30},
    {"label": "应付合计", "amount": 871.27}
  ]
}
```

### 用量

```
GET  /api/v1/pricing/usage?user_id=123&tier=free
GET  /api/v1/pricing/usage/history?user_id=123&usage_key=matches_performed&months=6
```

### 订阅变更

```
POST /api/v1/pricing/upgrade
```

请求体:
```json
{
  "user_id": 123,
  "target_tier": "pro",
  "billing_cycle": "monthly",
  "auto_renew": true
}
```

### 账单

```
GET  /api/v1/pricing/invoice?user_id=123&page=1&limit=20
```

### 管理

```
POST /api/v1/pricing/reload
```

## 各层定价详情

### Free (免费版) — ¥0

| 功能 | 配额 |
|------|------|
| 名片 | 5 张 |
| 匹配次数 | 10 次/月 |
| AI 聊天 | 20 次/月 |
| NFC 写入 | ✗ |
| API 访问 | ✗ |
| 存储空间 | 50 MB |

### Pro (专业版) — ¥99/月

| 功能 | 配额 |
|------|------|
| 名片 | 100 张 |
| 匹配次数 | 500 次/月 |
| AI 聊天 | 1000 次/月 |
| NFC 写入 | ✓ |
| CRM 导出 | ✓ (500行/月) |
| 团队成员 | 3 人 |
| 存储空间 | 500 MB |

### Enterprise (企业版) — ¥499/月

| 功能 | 配额 |
|------|------|
| 名片 | 1000 张 |
| 匹配次数 | 无限制 |
| AI 聊天 | 无限制 |
| NFC 写入 | ✓ |
| API 访问 | ✓ |
| CRM 导出 | ✓ (无限制) |
| 自定义品牌 | ✓ |
| 优先支持 | ✓ |
| 专属经理 | ✓ |
| 团队成员 | 无限制 |
| 存储空间 | 10 GB |

## 附加包 (Add-on)

| 包名 | 单价 | 最小购买 | 价格 |
|------|------|----------|------|
| 额外名片包 | ¥5/张 | 10张 | ¥30 |
| 额外匹配包 | ¥1/次 | 50次 | ¥30 |
| 扩容存储包 | ¥0.1/MB | 1GB | ¥50 |
| AI 聊天充值包 | ¥0.3/次 | 100次 | ¥20 |

## 优惠与折扣

| 类型 | 说明 |
|------|------|
| 年付折扣 | 省约1个月费用 (≈16.67%) |
| 首月优惠 | 新用户 Pro 版首月仅 ¥9.9 |
| 推荐奖励 | 推荐人获 ¥50 余额，被推荐人首单85折 |
| 优惠券 | CHAINKEWELCOME(¥50), STARTUP50(5折), BETA100(¥100) |

## 集成指南

### Python 代码调用

```python
from app.services.pricing_engine import get_pricing_engine
from app.services.usage_tracker import UsageTracker
from app.database import get_db

# 报价计算
engine = get_pricing_engine()
quote = engine.calculate_quote("pro", "yearly", coupon_code="CHAINKEWELCOME")

# 配额检查
quota = engine.check_quota("pro", "matches_per_month", current_usage=120, additional_units=1)

# 用量记录
db = next(get_db())
tracker = UsageTracker(db)
tracker.record_usage(user_id=123, usage_key="matches_performed", units=1)

# 用量摘要
summary = tracker.get_usage_summary(user_id=123, tier="pro")
```

### 中间件集成 (自动用量追踪)

在需要追踪的功能入口调用 UsageTracker.record_usage():

```python
# 在匹配引擎中
from app.services.usage_tracker import get_usage_tracker

tracker = get_usage_tracker(db)
tracker.record_usage(user_id, "matches_performed", 1)

# 在 API 调用中
tracker.record_usage(user_id, "api_calls", 1)
```

## 测试

```bash
# Python 语法检查
python -m py_compile app/services/pricing_engine.py
python -m py_compile app/services/usage_tracker.py
python -m py_compile app/routers/pricing.py

# YAML 语法检查
python -c "import yaml; yaml.safe_load(open('config/pricing.yaml'))"

# 运行测试
pytest tests/ -k "pricing or usage" -v
```

## 增量式设计原则

1. **不修改现有代码**: 所有新增功能以独立文件存在
2. **不破坏现有路由**: billing.py / subscription.py / recharge.py 保持不变
3. **单例模式**: PricingEngine 全局单例，不重复加载
4. **YAML 驱动**: 配置修改无需改代码
5. **热加载**: 配置变更可在线生效
6. **惰性建表**: 用量表在使用时自动创建
