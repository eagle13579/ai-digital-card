# 付款转化分析 (Payment Analytics)

## 概述

付款转化分析模块提供从数据库实时聚合的付费转化漏斗指标，供运营仪表盘和 API 查询。

## 指标定义

| 指标 | 英文名 | 定义 | 数据源 |
|------|--------|------|--------|
| 试用启动数 | Trial Start | 创建 TrialRecord 的用户数 | `trial_records` 表 |
| 试用转化率 | Trial Conversion | 付费转化用户数 / 总试用用户数 × 100% | `trial_records.converted_at` |
| 月度经常性收入 | MRR | 活跃付费订阅的月度费用总和 | `enterprise_subscriptions` × `PLANS` 定价 |
| 月度流失率 | Churn Rate | (过期未续费 + 主动取消) / 期初活跃用户 × 100% | `enterprise_subscriptions` 状态 |
| 生命周期价值 | LTV | 总付费收入 / 唯一付费用户数 | `payment_orders` + 去重 user_id |

## API

### GET /api/analytics/payment/overview

返回所有付款指标的总览。

**请求示例:**

```bash
curl http://localhost:8201/api/analytics/payment/overview
```

**响应结构:**

```json
{
  "code": 200,
  "message": "ok",
  "data": {
    "trial": {
      "total_trials": 120,
      "active_trials": 45,
      "converted": 30,
      "expired": 45,
      "conversion_rate_pct": 25.0,
      "recent_30d_trials": 18
    },
    "mrr": {
      "total_mrr_cents": 199800,
      "total_mrr_yuan": 1998.0,
      "active_subscriptions": 42,
      "tier_breakdown": {
        "standard": { "count": 35, "mrr_cents": 9900 },
        "enterprise": { "count": 7, "mrr_cents": 49900 }
      }
    },
    "churn_rate": {
      "churn_rate_30d_pct": 5.2,
      "churned_30d": 3,
      "expired_30d": 2,
      "cancelled_30d": 1,
      "expiring_30d": 5,
      "active_before_30d": 58
    },
    "ltv": {
      "total_paid_orders": 156,
      "total_revenue_cents": 998000,
      "total_revenue_yuan": 9980.0,
      "unique_payers": 42,
      "avg_ltv_cents": 23761,
      "avg_ltv_yuan": 237.61
    },
    "paid_users": {
      "tier_distribution": {
        "standard": 35,
        "enterprise": 7,
        "free": 200
      },
      "total_paid": 42
    },
    "calculated_at": "2026-07-02T12:00:00"
  }
}
```

## 数据流

```
┌─────────────┐   ┌──────────────────────┐   ┌─────────────────────┐
│  TrialRecord │   │ EnterpriseSubscription│   │   PaymentOrder      │
│  (试用记录)   │   │   (订阅记录)          │   │   (支付订单)         │
├─────────────┤   ├──────────────────────┤   ├─────────────────────┤
│ user_id     │   │ user_id              │   │ user_id             │
│ status      │   │ tier                 │   │ status (paid)       │
│ converted_at│   │ status (active/trial) │   │ total_cents         │
│ started_at  │   │ price_cents          │   └─────────────────────┘
└─────────────┘   │ start_date/end_date  │
                   └──────────────────────┘
                              │
                              ▼
                   ┌──────────────────────┐
                   │ PaymentAnalyticsService│
                   │  (payment_analytics.py)│
                   │  ├ get_overview()      │
                   │  ├ _get_trial_stats()  │
                   │  ├ _calc_mrr()         │
                   │  ├ _calc_churn_rate()  │
                   │  ├ _calc_ltv()         │
                   │  └ _get_paid_stats()   │
                   └──────────────────────┘
                              │
                              ▼
                   ┌──────────────────────┐
                   │ GET /api/analytics/    │
                   │ payment/overview       │
                   └──────────────────────┘
```

## 依赖

- `app.models.payment.PaymentOrder`
- `app.models.payment.EnterpriseSubscription`
- `app.models.payment.TrialRecord`
- `app.services.subscription_service.PLANS`

## 扩展

如需新增指标，在 `PaymentAnalyticsService` 类中添加 `_calc_xxx()` 方法，
然后在 `get_overview()` 中调用并返回。

### 常见扩展需求

1. **按时间范围过滤** — 给 `get_overview` 添加 `start_date`/`end_date` 参数
2. **按套餐过滤** — 添加 `tier` 参数筛选指定套餐的数据
3. **同比/环比** — 增加 `_calc_mom()` 和 `_calc_yoy()` 方法
4. **ARPU (每用户平均收入)** — `total_revenue / active_users`
5. **NRR (净收入留存率)** — `(起始MRR + 升级 - 降级 - 流失) / 起始MRR`
