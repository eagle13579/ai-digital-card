# AI 数智名片 — 全球架构与 1 亿用户水平扩展最佳实践

> **文档状态**: v1.0 · 2026-07-01  
> **适用场景**: AI 数字名片 SaaS 平台的全球部署、CRM 多态连接、超大规模水平扩展  
> **覆盖范围**: CRM 多态连接层 · 1 亿用户架构 · 海外 API 容错 · 分阶段路线图 · 成本/复杂度/收益权衡

---

## 目录

1. [架构全景](#1-架构全景)
2. [CRM 多态连接层（核心架构模式）](#2-crm-多态连接层核心架构模式)
3. [1 亿用户水平扩展架构](#3-1-亿用户水平扩展架构)
4. [海外 API 不可达的容错策略](#4-海外-api-不可达的容错策略)
5. [数据层设计](#5-数据层设计)
6. [安全与合规](#6-安全与合规)
7. [分阶段实施路线图](#7-分阶段实施路线图)
8. [成本模型与 Trade-off 总览](#8-成本模型与-trade-off-总览)
9. [附录：关键代码模式](#9-附录关键代码模式)

---

## 1. 架构全景

```
                                  ┌──────────────────────────────┐
                                  │       用户终端 (微信/Web/App)      │
                                  └──────────┬───────────────────┘
                                             │
                                    ┌────────▼────────┐
                                    │   CDN / 全球加速    │
                                    │ 阿里云CDN(中国)     │
                                    │ CloudFront(海外)   │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │   Kong API 网关    │ ← 多区域路由、限流、鉴权
                                    └────────┬────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        │                        │
            ┌───────▼───────┐       ┌───────▼───────┐       ┌───────▼───────┐
            │  阿里云(中国)   │       │   AWS(海外)    │       │   GCP(备)      │
            │  cn-hangzhou  │       │  us-east-1    │       │  europe-west1 │
            └───────┬───────┘       └───────┬───────┘       └───────┬───────┘
                    │                        │                        │
            ┌───────▼───────┐       ┌───────▼───────┐       ┌───────▼───────┐
            │  K8s 集群      │       │  K8s 集群      │       │  K8s 集群      │
            │ ┌───────────┐ │       │ ┌───────────┐ │       │ ┌───────────┐ │
            │ │ API Pods  │ │       │ │ API Pods  │ │       │ │ API Pods  │ │
            │ │ Worker    │ │       │ │ Worker    │ │       │ │ Worker    │ │
            │ │ AI推理    │ │       │ │ AI推理    │ │       │ │ AI推理    │ │
            │ └───────────┘ │       │ └───────────┘ │       │ └───────────┘ │
            └───────┬───────┘       └───────┬───────┘       └───────┬───────┘
                    │                        │                        │
         ┌──────────┴──────────┐   ┌─────────┴─────────┐   ┌────────┴────────┐
         │  PostgreSQL Shard   │   │  PostgreSQL Shard  │   │  PostgreSQL Shard│
         │  Redis Cluster      │   │  Redis Cluster     │   │  Redis Cluster   │
         │  Kafka (跨域同步)    │   │  Kafka (跨域同步)   │   │  Kafka (跨域同步) │
         └─────────────────────┘   └───────────────────┘   └─────────────────┘
                    │                        │                        │
                    └────────────────────────┼────────────────────────┘
                                             │
                                    ┌────────▼────────┐
                                    │  CRM 多态连接层    │
                                    │  (适配器模式)     │
                                    └────────┬────────┘
                                             │
         ┌────────────────┬──────────────────┼──────────────────┬────────────────┐
         │                │                  │                  │                │
   ┌─────▼─────┐  ┌──────▼─────┐  ┌────────▼──────┐  ┌───────▼───────┐  ┌──────▼──────┐
   │ Salesforce │  │  HubSpot   │  │ 纷享销客(中国) │  │ 企业微信/钉钉  │  │自托管存储     │
   │  (海外)    │  │  (海外)    │  │ 销售易(中国)   │  │   (中国)      │  │ Supabase/    │
   └────────────┘  └────────────┘  └───────────────┘  └───────────────┘  │ CouchDB      │
                                                                         └─────────────┘
```

### 核心设计原则

| 原则 | 说明 |
|:-----|:------|
| **无状态设计** | 所有应用节点无状态，水平扩展无需重启 |
| **区域自治** | 每个区域独立运行，区域故障不影响其他区域 |
| **优雅降级** | 外部服务不可达时自动降级，不中断核心业务流程 |
| **数据主权** | 中国用户数据留在阿里云，海外用户数据留在 AWS/GCP |
| **按量付费** | 从单体到全球多活的每一阶段都有对应的成本控制 |

---

## 2. CRM 多态连接层（核心架构模式）

### 2.1 抽象接口：`CrmAdapter`

```
┌─────────────────────────────────────────────────┐
│                 CrmAdapter (ABC)                  │
├─────────────────────────────────────────────────┤
│ + authenticate() -> bool                         │
│ + get_contact(id) -> Optional[ContactData]       │
│ + search_contacts(query, limit) -> list          │
│ + create_contact(data) -> SyncResult             │
│ + update_contact(data) -> SyncResult             │
│ + delete_contact(id) -> SyncResult               │
│ + sync_contacts(list, strategy) -> SyncResult    │
│ + health_check() -> dict                         │
│ + webhook_verify(payload) -> bool                │
│ + webhook_parse(payload) -> WebhookEvent         │
└──────────────┬────────────────┬─────────────────┘
               │                │
    ┌──────────┴───┐    ┌──────┴──────────┐
    │  海 外 实 现   │    │  中 国 实 现     │
    │ Salesforce   │    │ 纷享销客Adapter  │
    │ HubSpot      │    │ 销售易Adapter    │
    │ Pipedrive    │    │ 企业微信Adapter   │
    │              │    │ 钉钉Adapter      │
    └──────────────┘    └─────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │  自托管实现 (零外部依赖) │
                    │ Supabase / CouchDB │
                    │ (本地联系人存储)     │
                    └───────────────────┘
```

所有 CRM 集成继承自统一的 `CrmAdapter` 抽象基类，确保接口一致、可替换。

### 2.2 实现矩阵

| 适配器 | 区域 | 依赖 | 备注 |
|:-------|:-----|:------|:------|
| `SalesforceAdapter` | 海外 | REST API + OAuth2 | 企业级成熟方案 |
| `HubSpotAdapter` | 海外 | REST API + API Key | SMB 友好 |
| `PipedriveAdapter` | 海外 | REST API | 轻量级备选 |
| `纷享销客Adapter` | 中国 | HTTP API + Token | 国内 CRM 市占率领先 |
| `销售易Adapter` | 中国 | HTTP API + OAuth2 | 国内 CRM 备选 |
| `企业微信Adapter` | 中国 | 企微开放平台 API | 微信生态天然集成 |
| `钉钉Adapter` | 中国 | 钉钉开放平台 API | 钉钉生态集成 |
| `SupabaseCrmAdapter` | 自托管 | PostgreSQL（本地） | 零外部依赖，始终可用 |
| `CouchDBCrmAdapter` | 自托管 | CouchDB（本地） | 离线优先，P2P 同步 |

### 2.3 自动发现与选择

从 `.env` 配置自动选择适配器，不硬编码：

```python
# config/crm_config.py
import os
from typing import Optional
from .adapters import (
    CrmAdapter,
    SalesforceAdapter,
    HubSpotAdapter,
    PipedriveAdapter,
    FenxiangxiaokeAdapter,
    XiaoshouyiAdapter,
    WecomAdapter,
    DingtalkAdapter,
    SupabaseCrmAdapter,
)

class CrmAdapterFactory:
    """CRM 适配器工厂 — 根据环境变量自动发现并实例化适配器列表（有序）。"""

    PROVIDER_MAP = {
        "salesforce": SalesforceAdapter,
        "hubspot": HubSpotAdapter,
        "pipedrive": PipedriveAdapter,
        "fenxiangxiaoke": FenxiangxiaokeAdapter,
        "xiaoshouyi": XiaoshouyiAdapter,
        "wecom": WecomAdapter,
        "dingtalk": DingtalkAdapter,
        "supabase": SupabaseCrmAdapter,
    }

    @classmethod
    def create_ordered_chain(cls) -> list[CrmAdapter]:
        """按优先级返回已启用的适配器链。

        优先级由 CRM_ADAPTER_PRIORITY 环境变量控制，格式:
          CRM_ADAPTER_PRIORITY=salesforce,hubspot,fenxiangxiaoke,wecom,supabase

        未配置时自动探测可用服务。
        """
        priority_str = os.getenv("CRM_ADAPTER_PRIORITY", "")
        if priority_str:
            names = [n.strip() for n in priority_str.split(",") if n.strip()]
            return [
                cls.PROVIDER_MAP[name]()
                for name in names
                if name in cls.PROVIDER_MAP
            ]

        # 自动探测：按海外→中国→自托管顺序
        return cls._auto_detect_chain()

    @classmethod
    def _auto_detect_chain(cls) -> list[CrmAdapter]:
        chain = []
        # 海外 CRM (检测环境变量中的 API Key)
        if os.getenv("SALESFORCE_CLIENT_ID"):
            chain.append(SalesforceAdapter())
        if os.getenv("HUBSPOT_API_KEY"):
            chain.append(HubSpotAdapter())
        # 中国 CRM
        if os.getenv("FENXIANGXIAOKE_TOKEN"):
            chain.append(FenxiangxiaokeAdapter())
        if os.getenv("WECOM_CORP_ID"):
            chain.append(WecomAdapter())
        # 自托管 (始终可用)
        chain.append(SupabaseCrmAdapter())
        return chain
```

### 2.4 降级链（Degradation Chain）

```
                 ┌──────────────┐
                 │ 海外 CRM 请求  │
                 │ (Salesforce)  │
                 └──────┬───────┘
                        │
                 ┌──────▼───────┐
            YES  │ 海外可达？     │  NO
                 └──────┬───────┘
                        │
               ┌────────┴────────┐
               │                 │
        ┌──────▼──────┐  ┌──────▼──────┐
        │ Salesforce   │  │ 中国 CRM 可达？│
        │ API 调用     │  └──────┬──────┘
        └──────┬───────┘         │
               │           ┌─────┴─────┐
               │      YES  │           │ NO
               │           │           │
               │    ┌──────▼────┐ ┌────▼────┐
               │    │ 纷享销客/  │ │ 自托管   │
               │    │ 企业微信   │ │ Supabase │
               │    └─────┬─────┘ └────┬────┘
               │          │            │
               │          │      ┌─────▼─────┐
               │          │      │ 本地缓存    │
               │          │      │ (Redis TTL)│
               │          │      └───────────┘
               │          │
               │    ┌─────▼──────────┐
               │    │ 异步补偿任务     │
               │    │ (当海外恢复后回写)│
               │    └───────────────┘
               │
         ┌─────▼──────────┐
         │ 返回统一响应格式 │
         └────────────────┘
```

**降级策略关键逻辑**:

1. **同步调用链**: 按优先级依次尝试，第一个成功的返回
2. **异步补偿**: 降级到低优先级时，向 Kafka 发送补偿事件；当高优先级恢复后自动回写
3. **存量过期**: 自托管/本地缓存的数据带有 TTL（默认 15 分钟），超时后需重新同步
4. **用户透明**: 最终用户无感，仅后端日志记录降级事件

### 2.5 Webhook 多态处理

```python
# 统一 Webhook 入口
@router.post("/crm/webhook/{provider}")
async def crm_webhook(provider: str, payload: dict):
    adapter = CrmAdapterFactory.create_by_name(provider)
    if not adapter.webhook_verify(payload):
        raise HTTPException(403, "Webhook 签名验证失败")
    event = adapter.webhook_parse(payload)
    # 统一事件处理
    await handle_crm_event(event)
    return {"status": "ok"}
```

### 2.6 Trade-off 分析

| 方案 | 成本 | 复杂度 | 收益 |
|:-----|:-----|:-------|:-----|
| 只对接 Salesforce/HubSpot | 低（1-2人周） | 低 | 快速上线，但中国用户不可用 |
| 全适配器实现（8+） | 高（4-6人周） | 中高 | 全球全覆盖，无服务盲区 |
| 适配器工厂 + 自动降级 | 中（2-3人周增量） | 中 | 高可用，优雅故障处理 |
| 自托管存储替代 CRM | 低（开发成本） | 低 | 零外部依赖，但无 CRM 高级功能 |

**推荐**: 阶段一 (现在) 实现 Salesforce + HubSpot + 自托管 Supabase 三链降级；阶段二 (3个月) 加入纷享销客 + 企业微信；阶段三 (6个月) 完善全部适配器。

---

## 3. 1 亿用户水平扩展架构

### 3.1 多区域部署拓扑

```
全球用户
    │
    ├─ 中国大陆 ─── 阿里云 (cn-hangzhou / cn-shanghai / cn-beijing)
    │                 ├── api.digital-card.cn (备案域名)
    │                 ├── PostgreSQL 主库 (阿里云 RDS for PostgreSQL)
    │                 ├── Redis 集群 (阿里云 Redis 企业版)
    │                 ├── 阿里云 Kafka (消息队列)
    │                 ├── 阿里云 CDN (静态资源加速)
    │                 └── K8s 集群 (阿里云 ACK)
    │
    ├─ 亚太 ─────── AWS ap-southeast-1 (新加坡) / GCP asia-east1 (台湾)
    ├─ 北美 ─────── AWS us-east-1 (弗吉尼亚) / us-west-2 (俄勒冈)
    └─ 欧洲 ─────── AWS eu-west-1 (爱尔兰) / eu-central-1 (法兰克福)
                      ├── api.digital-card.ai (海外域名)
                      ├── PostgreSQL 分片 (RDS Aurora / Cloud SQL)
                      ├── Redis Cluster (ElastiCache / Memorystore)
                      ├── Kafka (MSK / Confluent Cloud)
                      ├── CloudFront CDN
                      └── K8s 集群 (EKS / GKE)
```

### 3.2 数据库分片策略

#### 按 `user_id` 哈希分片

```
用户总量: 100,000,000
初始分片数: 32 (每片 ~310 万用户)
最大分片数: 4096 (每片 ~2.4 万用户)

分片算法: user_id % num_shards
rebalance 策略: 虚拟节点一致性哈希 (Pre-split + 逐步扩容)

┌─────────┬─────────┬─────────┬─────────┐
│ Shard 0 │ Shard 1 │ Shard 2 │ Shard 3 │  ... → Shard N
│ us-east │ us-east │ eu-west │ cn-hz   │
│ 主:RDS  │ 主:RDS  │ 主:RDS  │ 主:RDS  │
│ 从: ×2  │ 从: ×2  │ 从: ×2  │ 从: ×2  │
└─────────┴─────────┴─────────┴─────────┘
     │         │         │         │
     └─────────┴─────────┴─────────┘
               │
        ProxySQL / pgcat (DB 连接池 & 路由)
               │
        ┌──────┴──────┐
        │  API Pods   │
        └─────────────┘
```

#### 读写分离

```
                     ┌───────────┐
                     │  API Pod  │
                     └─────┬─────┘
                           │
                    ┌──────┴───────┐
                    │  读/写路由    │
                    │ (SQL解析)    │
                    └───┬─────┬───┘
                        │     │
               ┌────────┘     └────────┐
               │                       │
        ┌──────▼──────┐        ┌──────▼──────┐
        │  主库 (写入)  │        │  从库 (读取)   │
        │  PostgreSQL │        │  PostgreSQL  │
        │  RDS 主实例  │        │  RDS 只读副本  │
        └─────────────┘        └─────────────┘
                                     │
                              ┌──────┴──────┐
                              │  只读连接池   │
                              │ (1主→N从)    │
                              └─────────────┘
```

### 3.3 缓存策略 (Redis Cluster)

| 缓存层级 | 用途 | TTL | 容量预估 (1亿用户) |
|:---------|:-----|:----|:-------------------|
| L1: 本地内存缓存 | 热点用户名片、当前会话 | 60s | ~1GB per Pod |
| L2: Redis Cluster | 用户会话、名片数据、API 响应 | 5-30min | ~200GB |
| L3: CDN | 静态资源 (JS/CSS/图片) | 7d | 前置 CDN 无上限 |

**Redis 集群规划**:

```
每区域独立部署 Redis Cluster
初始: 3主3从 (6节点)
1亿用户: 18主18从 (36节点), 每节点 ~11GB

Key 设计:
  user:{user_id}:profile    → 用户名片 JSON
  user:{user_id}:session    → 会话 Token
  card:{card_id}:view_count → 访问计数 (写密集型, 用 Redis HyperLogLog)
  crm:{provider}:sync_token → CRM 同步游标
  rate_limit:{ip}:{endpoint}→ 速率限制计数器
```

### 3.4 消息队列 (Kafka 跨区域数据同步)

```
区域 A (阿里云)                   区域 B (AWS)
┌──────────────┐               ┌──────────────┐
│ Producer     │               │ Producer     │
│ (创建名片)    │               │ (修改名片)    │
└──────┬───────┘               └──────┬───────┘
       │                              │
       │   ┌──────────────────────┐   │
       │   │   Kafka MirrorMaker  │   │
       └──►│  跨区域双向同步       │◄──┘
           │  topic: user-events  │
           │  topic: crm-events   │
           │  topic: ai-results   │
           │  topic: billing      │
           └────────┬─────────────┘
                    │
           ┌────────▼────────┐
           │ Consumer Group   │
           │ (每区域一个)      │
           │ - 更新 Elasticsearch│
           │ - 触发 Webhook   │
           │ - 发送通知       │
           │ - 异步 AI 处理   │
           └─────────────────┘
```

**Topic 设计**:

| Topic | 分区数 | 保留策略 | 用途 |
|:------|:-------|:---------|:-----|
| `user-events` | 32 | 7天 | 用户创建/更新/删除跨域同步 |
| `crm-events` | 16 | 3天 | CRM 同步补偿事件 |
| `ai-results` | 16 | 1天 | AI 异步处理结果 |
| `billing` | 8 | 90天 | 账单与支付事件 |
| `notification` | 8 | 1天 | 推送通知队列 |
| `analytics` | 16 | 30天 | 用户行为埋点 |

### 3.5 API 网关 (Kong)

```
                          ┌─────────────┐
                          │   Global     │
                          │   Kong CP    │
                          │  (控制面)    │
                          └──────┬──────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
┌───────▼───────┐        ┌───────▼───────┐        ┌───────▼───────┐
│ Kong DP (中国) │        │ Kong DP (美国) │        │ Kong DP (欧洲) │
│ 阿里云         │        │  AWS         │        │  AWS          │
├───────────────┤        ├───────────────┤        ├───────────────┤
│ 路由规则:      │        │ 路由规则:      │        │ 路由规则:      │
│ *.cn → 阿里云  │        │ *.ai → AWS   │        │ *.ai → AWS EU │
│ 中国用户优化   │        │ 海外用户优化    │        │ GDPR 合规路由  │
└───────┬───────┘        └───────┬───────┘        └───────┬───────┘
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  Kong 全局插件           │
                    │  - Rate Limiting (区域级) │
                    │  - JWT/OAuth2 鉴权       │
                    │  - Prometheus 指标       │
                    │  - 请求/响应日志          │
                    │  - CORS                  │
                    │  - 灰度/金丝雀发布        │
                    └─────────────────────────┘
```

### 3.6 无状态服务设计

```
┌─────────────────────────────────────────────────┐
│               API Service (FastAPI)              │
├─────────────────────────────────────────────────┤
│ 无状态: ✓                                       │
│   - 不存储本地文件 (上传→OSS/S3)                   │
│   - 不存储本地 Session (Redis 集中存储)            │
│   - 不依赖 Pod 本地磁盘 (临时可销毁)                │
│                                                  │
│ 水平扩展: HPA (CPU > 60% → scale up, 下限2→100)   │
│   - 1万用户: 2 Pod → 4 Pod                       │
│   - 100万用户: 8 Pod → 16 Pod                    │
│   - 1亿用户: 100 Pod → 500 Pod                   │
│                                                  │
│ 优雅关闭: terminationGracePeriodSeconds=60       │
│   - SIGTERM → 停止接受新请求 → 完成处理中请求 → 退出  │
└─────────────────────────────────────────────────┘
```

### 3.7 CDN 策略

| 区域 | CDN 提供商 | 加速内容 | 源站 |
|:-----|:-----------|:---------|:-----|
| 中国内地 | 阿里云 CDN | 前端静态资源、名片图片 | 阿里云 OSS |
| 中国香港/澳门/台湾 | CloudFront + 阿里云CDN海外节点 | 同上 | AWS S3 (同步自OSS) |
| 亚太 | CloudFront | 同上 | AWS S3 |
| 北美 | CloudFront | 同上 | AWS S3 |
| 欧洲 | CloudFront | 同上 | AWS S3 (欧盟节点) |

### 3.8 Trade-off 分析

| 方案 | 成本（月） | 复杂度 | 收益 |
|:-----|:----------|:-------|:-----|
| **单体** (当前) | ~$200-500 | 低 | 快速验证，迭代快 |
| **1主库+只读副本** (1万用户) | ~$1K-3K | 低 | 性价比高，够用 |
| **分片+多区域** (10万用户) | ~$10K-30K | 中 | 用户体验好，可用性高 |
| **全球多活+跨域同步** (100万+) | ~$50K-200K+ | 高 | 真正全球高可用 |

**推荐**:

- **0→1万用户**: 单体 + PostgreSQL 单实例 + Redis
- **1万→10万**: 读写分离 + Redis Cluster + K8s HPA
- **10万→100万**: 数据库分片 + 多区域 + Kafka 跨域同步
- **100万→1亿**: 全球多活 + 分片扩容 + 自动扩缩

---

## 4. 海外 API 不可达的容错策略

### 4.1 AI API 多回退链

```
┌─────────────────────────────────────────────────────────────────────┐
│                      AI 推理请求                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  策略一: 地理感知路由 (默认)                                    │  │
│  │                                                                 │  │
│  │  中国用户 → DeepSeek (中国可直达, 延迟 <50ms)                   │  │
│  │            ↓ 不可达 → 百度文心一言 → 阿里通义千问 → 本地小模型   │  │
│  │                                                                 │  │
│  │  海外用户 → OpenAI / Anthropic (海外可达, 延迟 <100ms)          │  │
│  │            ↓ 不可达 → DeepSeek API (海外节点) → 本地小模型       │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  策略二: API 代理转发 (合规路径)                                │  │
│  │                                                                 │  │
│  │  阿里云 API 网关 → 海外 API 代理（阿里云国际站合规方案）        │  │
│  │  华为云 API 网关 → 海外 API 代理（华为云国际站合规方案）        │  │
│  │                                                                 │  │
│  │  限制: 需要额外成本，且某些服务受出口管制                       │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  策略三: 本地模型兜底 (始终可用)                                │  │
│  │                                                                 │  │
│  │  Qwen2.5-7B / DeepSeek-R1-Distill 本地部署                     │  │
│  │  覆盖: OCR、名片摘要、标签提取                                   │  │
│  │  限制: 复杂推理能力远低于云端 LLM                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**代码实现**:

```python
# ai/ai_router.py
from typing import Optional, Callable, Any
import logging

logger = logging.getLogger(__name__)

class AIRouter:
    """AI 服务智能路由器 — 支持多提供商回退和地理感知。"""

    def __init__(self, user_region: str):
        self.user_region = user_region  # "cn" | "overseas"
        self._build_chain()

    def _build_chain(self):
        """根据用户区域构建优先级链。"""
        if self.user_region == "cn":
            self.providers = [
                ("deepseek", self._call_deepseek),
                ("baidu_wenxin", self._call_baidu_wenxin),
                ("ali_qwen", self._call_ali_qwen),
                ("local_qwen2.5", self._call_local_model),
            ]
        else:
            self.providers = [
                ("openai", self._call_openai),
                ("anthropic", self._call_anthropic),
                ("deepseek_overseas", self._call_deepseek_overseas),
                ("local_qwen2.5", self._call_local_model),
            ]

    async def chat(self, messages: list[dict], **kwargs) -> dict[str, Any]:
        """调用 AI 链，依次尝试直到成功。"""
        last_error = None
        for name, caller in self.providers:
            try:
                result = await caller(messages, **kwargs)
                logger.info("AI 调用成功: provider=%s region=%s", name, self.user_region)
                return {"provider": name, "data": result}
            except Exception as e:
                last_error = e
                logger.warning("AI 调用失败: provider=%s error=%s", name, str(e))
                continue

        logger.error("所有 AI 提供商均不可达")
        return {"provider": None, "error": str(last_error), "fallback": True}

    # 各提供商的具体实现省略...
```

### 4.2 CRM 多回退链 (已在第2章详述)

**总结**: Salesforce → HubSpot → 纷享销客 → 企业微信 → Supabase(自托管) → Redis 缓存

### 4.3 海外 API 代理 (合规镜像)

```
┌────────────┐     ┌─────────────────┐     ┌──────────────┐
│ 中国用户    │────►│ 阿里云 API 网关  │────►│ OpenAI 镜像    │
│            │     │                 │     │ (阿里云国际)  │
│            │     │ 或              │     │              │
│            │     │ 华为云 API 网关  │     │ 合规 SD-WAN   │
└────────────┘     └─────────────────┘     └──────────────┘
```

**两种合规路径**:

| 方案 | 提供商 | 延迟增加 | 成本 | 合规性 |
|:-----|:-------|:---------|:-----|:-------|
| 云厂商官方 API 代理 | 阿里云/华为云 API 网关 | +10-30ms | 低（按量） | 完全合规 |
| 自建 SD-WAN 隧道 | 专线/VPN（合规备案） | +5-15ms | 中（固定月费） | 需备案 |
| 不代理（直接阻断） | — | — | 零成本 | 中国用户无法使用 |

### 4.4 降级对用户体验的影响

| 场景 | 正常体验 | 降级体验 | 是否可接受 |
|:-----|:---------|:---------|:-----------|
| DeepSeek → 文心一言 | 名片识别精准 | 识别率下降~5% | ✅ 可接受 |
| 所有 AI 不可达 → 本地模型 | 智能识别 | 仅基础 OCR | ⚠️ 临时可接受 |
| Salesforce → 纷享销客 | 实时同步 | 同步延迟 +10s | ✅ 可接受 |
| Salesforce → 自托管 | 实时同步 | 无法推送至海外 CRM | ⚠️ 降级但可用 |
| 所有 CRM 不可达 → 本地缓存 | 可写可读 | 数据最终一致 | ⚠️ 临时可接受 |

### 4.5 Trade-off 分析

| 容错策略 | 成本 | 复杂度 | 收益 |
|:---------|:-----|:-------|:-----|
| 多 AI 提供商回退 | 中（多 API 订阅费） | 中 | 高可用，用户无感 |
| 本地模型兜底 | 高（GPU 服务器） | 中高 | 完全独立，零外部依赖 |
| 云厂 API 代理 | 低（按量计费） | 低 | 合规访问海外 API |
| CRM 降级链 | 低（仅开发成本） | 中 | 业务连续性保障 |
| 本地缓存 + 异步补偿 | 低 | 低 | 最终一致性，始终可用 |

---

## 5. 数据层设计

### 5.1 数据库表结构（面向 1 亿用户优化）

```sql
-- ── 用户分片表 (按 user_id % shard_count 分布) ──

CREATE TABLE users (
    user_id         BIGSERIAL PRIMARY KEY,       -- 全局唯一, 分片键
    email           VARCHAR(255) UNIQUE,
    phone           VARCHAR(20),
    password_hash   VARCHAR(255),
    display_name    VARCHAR(100),
    avatar_url      TEXT,
    region          VARCHAR(10) NOT NULL DEFAULT 'cn',  -- cn / us / eu / ap
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ                      -- 软删除
);
-- 索引: CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;

CREATE TABLE digital_cards (
    card_id         BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(user_id),
    title           VARCHAR(200),
    subtitle        VARCHAR(200),
    company         VARCHAR(200),
    position        VARCHAR(200),
    phone           VARCHAR(20),
    email           VARCHAR(255),
    website         VARCHAR(500),
    address         TEXT,
    social_links    JSONB,           -- {wechat, linkedin, twitter, ...}
    qr_code_url     TEXT,
    theme           VARCHAR(50),
    ai_summary      TEXT,            -- AI 生成的智能摘要
    ocr_metadata    JSONB,           -- OCR 原始识别结果
    is_public       BOOLEAN DEFAULT true,
    view_count      BIGINT DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- 索引: CREATE INDEX idx_cards_user ON digital_cards(user_id);
-- 索引: CREATE INDEX idx_cards_company ON digital_cards(company);

CREATE TABLE crm_sync_logs (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL,
    provider        VARCHAR(50) NOT NULL,   -- salesforce / hubspot / fenxiangxiaoke
    action          VARCHAR(20) NOT NULL,   -- export / update / delete / sync
    status          VARCHAR(20) NOT NULL,   -- success / failed / degraded
    contact_data    JSONB,
    error_message   TEXT,
    latency_ms      INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
PARTITION BY RANGE (created_at);
-- 按时间分区, 保留 90 天, 自动清理

-- ── 全局表 (不分区, 保存在每个区域) ──

CREATE TABLE global_config (
    key             VARCHAR(100) PRIMARY KEY,
    value           JSONB NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE audit_log (
    id              BIGSERIAL,
    user_id         BIGINT,
    action          VARCHAR(50) NOT NULL,
    resource_type   VARCHAR(50),
    resource_id     VARCHAR(100),
    detail          JSONB,
    ip_address      INET,
    user_agent      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);
```

### 5.2 跨区域数据同步策略

```
更新发生区域 (Region A)
        │
        ├── 1. 写入本地数据库主库
        ├── 2. 写入本地 Kafka (user-events topic)
        │
        └── Kafka Connect (Debezium) CDC
                │
                ├── 捕获 PostgreSQL WAL 变更
                └── 发送到跨区域 Kafka MirrorMaker
                        │
                        ├── Region B Kafka → Region B PostgreSQL (从库)
                        ├── Region C Kafka → Region C PostgreSQL (从库)
                        └── 更新全局 Elasticsearch 索引
```

**一致性模型**: 最终一致性。CRDT (Conflict-free Replicated Data Types) 处理冲突：
- 名片内容: 最后写入者获胜 (LWW)
- 计数值: 合并加和
- 用户资料: 按字段级 LWW

### 5.3 Elasticsearch 全文搜索

```
写入管道:
  API Pod → Kafka (analytics) → Logstash → Elasticsearch → 搜索查询

索引策略:
  - 名片索引: 每秒~10K 文档写入
  - 分片数: 6 (2副本 × 3节点)
  - 热温架构: 7天热节点 → 30天温节点 → 90天删除

查询优化:
  - 搜索: name^5, company^3, title^2, description^1
  - 自动补全: edge_ngram + completion suggester
  - 多语言: ICU Analysis Plugin (中文/英文/日文等)
```

---

## 6. 安全与合规

### 6.1 数据主权

| 数据类型 | 中国用户 | 海外用户 |
|:---------|:---------|:---------|
| 用户个人资料 | 阿里云 RDS (中国) | AWS RDS (用户所在区域) |
| 名片数据 | 阿里云 RDS (中国) | AWS RDS (用户所在区域) |
| AI 分析结果 | 阿里云 (DeepSeek/文心) | AWS (OpenAI/Anthropic) |
| CRM 同步日志 | 各自区域存储 | 各自区域存储 |
| 支付记录 | 支付宝/微信 → 中国数据库 | Stripe → 海外数据库 |

### 6.2 合规要求

| 地区 | 法规 | 要求 |
|:-----|:-----|:------|
| 中国 | 《个人信息保护法》(PIPL) | 数据本地化, 用户同意, 跨境传输评估 |
| 欧洲 | GDPR | 数据可删除权, 数据可移植, DPA 处理协议 |
| 美国 | CCPA / HIPAA | 加州消费者隐私, 医疗数据保护 |
| 东南亚 | PDPA | 新加坡/泰国/马来西亚数据保护 |

### 6.3 安全架构要点

- **传输加密**: 全链路 HTTPS (TLS 1.3), 区域间 Kafka 通道 TLS
- **存储加密**: RDS 开启 TDE 透明加密, OSS/S3 服务端加密 (AES-256)
- **密钥管理**: 阿里云 KMS (中国) / AWS KMS (海外) — 每个区域独立
- **API 安全**: Kong 网关 JWT 鉴权 + 速率限制 + IP 白名单
- **审计日志**: 所有管理操作记录到 `audit_log` 表, 保留 180 天

---

## 7. 分阶段实施路线图

### 阶段 0: 现在 — 验证 & 夯实基础 (0 用户 → 1 万)

**目标**: 不改大架构，加 CRM 抽象层 + 降级逻辑

```
┌─────────────────────────────────────────────────┐
│  阶段 0 架构 (当前单体 + 新增 CRM 抽象层)         │
├─────────────────────────────────────────────────┤
│                                                   │
│  ┌──────────┐  ┌──────────┐  ┌────────────────┐ │
│  │  FastAPI │  │  SQLite  │  │  CrmAdapter     │ │
│  │  单体    │  │  (开发)  │  │  Salesforce     │ │
│  │          │  │  PgSQL   │  │  HubSpot        │ │
│  │          │  │  (生产)  │  │  Supabase(自托管)│ │
│  └──────────┘  └──────────┘  └────────────────┘ │
│                                                   │
│  部署: Docker Compose + 1台阿里云 ECS             │
│  成本: ~$200/月                                  │
│  团队: 2-3 后端                                  │
└─────────────────────────────────────────────────┘
```

**任务清单**:
- [ ] 将 `CrmAdapter` 抽象接口标准化 (已存在 `crm_base.py`, 需统一到新接口)
- [ ] 实现自动降级链 (海外→中国→自托管→缓存)
- [ ] 添加 `SupabaseCrmAdapter` 自托管实现
- [ ] API 响应缓存 (Redis, 即便单机也安装)
- [ ] 统一 `.env` 配置模板
- [ ] CRM 同步日志记录 (为后续 Kafka 做准备)

**交付物**:
- `backend/app/connectors/crm_base.py` — 统一抽象接口
- `backend/app/connectors/supabase_adapter.py` — 自托管实现
- `backend/app/services/crm_factory.py` — 自动发现工厂
- `backend/app/services/crm_chain.py` — 降级链执行器

### 阶段 1: 3 个月 — 1 万用户

**目标**: PostgreSQL + Redis + K8s

```
┌─────────────────────────────────────────────────┐
│  阶段 1 架构                                      │
├─────────────────────────────────────────────────┤
│                                                   │
│  ┌──────────┐  ┌────────────┐  ┌──────────────┐ │
│  │  K8s     │  │ PostgreSQL │  │  Redis        │ │
│  │  (ACK)   │  │  阿里云RDS  │  │  阿里云Redis  │ │
│  │  HPA 2→6 │  │  主+从库    │  │  集群 (3主3从)│ │
│  └──────────┘  └────────────┘  └──────────────┘ │
│                                                   │
│  ┌────────────────────────────────────────────┐  │
│  │  CRM 适配器: 全部 6+ 实现                    │  │
│  │  Salesforce / HubSpot / 纷享销客 / 企业微信  │  │
│  │  / 钉钉 / Supabase                          │  │
│  └────────────────────────────────────────────┘  │
│                                                   │
│  部署: 阿里云 K8s (ACK) + RDS PostgreSQL          │
│  成本: ~$1K-3K/月 (含 RDS 主+从)                  │
│  团队: 4-6 后端                                   │
└─────────────────────────────────────────────────┘
```

**迁移要点**:
- SQLite → PostgreSQL 数据迁移 (使用 Alembic)
- 单体 → K8s 容器化 (现有 Dockerfile 已准备)
- 引入 Redis 缓存层
- 所有 CRM 适配器实现完成

### 阶段 2: 6 个月 — 10 万用户

**目标**: 多区域部署 + Kafka + CDN + 读写分离

```
┌─────────────────────────────────────────────────┐
│  阶段 2 架构 (双区域)                             │
├─────────────────────────────────────────────────┤
│                                                   │
│  中国区 (阿里云)        海外区 (AWS)              │
│  ┌─────────────┐      ┌─────────────┐           │
│  │ K8s (ACK)   │      │ K8s (EKS)   │           │
│  │ 6-12 Pod    │      │ 6-12 Pod    │           │
│  ├─────────────┤      ├─────────────┤           │
│  │ RDS PgSQL   │      │ RDS Aurora  │           │
│  │ 主+2从      │      │ 主+2从      │           │
│  ├─────────────┤      ├─────────────┤           │
│  │ Redis 集群  │      │ Redis 集群  │           │
│  ├─────────────┤      ├─────────────┤           │
│  │ Kafka       │◄────►│ Kafka       │           │
│  │ (MirrorMaker)│      │(MirrorMaker)│           │
│  ├─────────────┤      ├─────────────┤           │
│  │ 阿里云CDN   │      │ CloudFront  │           │
│  └─────────────┘      └─────────────┘           │
│                                                   │
│  Kong API 网关 (双区域路由)                        │
│  成本: ~$10K-30K/月                              │
│  团队: 8-12 工程师 (含 SRE)                       │
└─────────────────────────────────────────────────┘
```

**迁移要点**:
- 数据库读写分离 (ProxySQL/pgcat)
- Kafka 跨区域同步 (MirrorMaker 2.0)
- CDN 加速配置
- Kong API 网关部署
- 蓝绿部署 + 金丝雀发布生产化

### 阶段 3: 12 个月 — 100 万+

**目标**: 全部分片 + 自动扩缩 + 多活

```
┌─────────────────────────────────────────────────┐
│  阶段 3 架构 (全球多活)                           │
├─────────────────────────────────────────────────┤
│                                                   │
│  阿里云 (cn)     AWS (us)      AWS (eu)         │
│  ┌───────┐      ┌───────┐      ┌───────┐       │
│  │Shard  │      │Shard  │      │Shard  │       │
│  │ 0-15  │      │ 16-31 │      │ 32-47 │       │
│  │ 主+从  │      │ 主+从  │      │ 主+从  │       │
│  └───────┘      └───────┘      └───────┘       │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │  全球 Elasticsearch (跨区域复制)              │ │
│  ├─────────────────────────────────────────────┤ │
│  │  Kafka: 32 分区, 跨 3 区域 MirrorMaker      │ │
│  ├─────────────────────────────────────────────┤ │
│  │  Redis: 每个区域独立, 总计 ~36 节点           │ │
│  ├─────────────────────────────────────────────┤ │
│  │  Kong: 全球 1 控制面 + N 数据面              │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
│  成本: ~$50K-200K+/月                            │
│  团队: 20+ 工程师                                │
└─────────────────────────────────────────────────┘
```

**迁移要点**:
- 数据库分片 (一致性哈希 + 虚拟节点)
- 全球多活架构 (Active-Active)
- 自动扩缩容 (Cluster Autoscaler + HPA)
- 混沌工程 (Chaos Mesh / Litmus)
- 成本优化 (预留实例 + Spot 实例混部)

### 里程碑总览

```
里程碑    时间    用户量      架构                         成本/月
──────── ────── ───────── ────────────────────────── ──────────
现在       0      0→1K      单体+SQLite+CRM抽象层       ~$200
1个月      1M     1K→5K     PostgreSQL+Redis+Docker    ~$500
3个月      3M     5K→10K    K8s+RDS+写分离             ~$1K-3K
6个月      6M     10K→100K  双区域+Kafka+CDN+仅读副本   ~$10K-30K
12个月    12M     100K→1M   全分片+多活+自动扩缩        ~$30K-80K
18个月    18M     1M→10M    全球多活+优化+混沌工程      ~$80K-200K
24个月    24M     10M→100M  持续优化+成本控制           ~$200K-500K
```

---

## 8. 成本模型与 Trade-off 总览

### 8.1 各阶段成本分布

| 组件 | 阶段0 (单体) | 阶段1 (1万用户) | 阶段2 (10万用户) | 阶段3 (1亿用户) |
|:-----|:------------|:----------------|:-----------------|:----------------|
| 计算 (K8s) | $50 | $300 | $3,000 | $30,000-80,000 |
| 数据库 (RDS) | $50 | $200 | $2,000 | $20,000-50,000 |
| Redis | $20 | $100 | $500 | $5,000-10,000 |
| Kafka | — | — | $500 | $3,000-8,000 |
| CDN | $10 | $30 | $500 | $3,000-10,000 |
| API 网关 | — | $50 | $200 | $2,000-5,000 |
| AI API 调用 | $30 | $200 | $2,000 | $20,000-50,000 |
| 存储 (OSS/S3) | $10 | $50 | $300 | $3,000-10,000 |
| 监控 & 日志 | $10 | $50 | $500 | $2,000-5,000 |
| 运维人工 | $0 (开发) | $500 | $3,000 | $15,000-30,000 |
| **合计** | **~$200** | **~$1K-3K** | **~$10K-30K** | **~$80K-250K** |

### 8.2 关键 Trade-off 总表

| 决策 | 选项 A | 选项 B | 推荐 |
|:-----|:-------|:-------|:-----|
| 数据库 | SQLite → PgSQL 单机 | 直接上 RDS 分片 | **阶段式迁移** |
| CRM 层 | 仅 Salesforce/HubSpot | 全适配器 8+ | **阶段 0 先 3 个, 逐步增加** |
| AI 回退 | 无回退, 不可用则报错 | 多链回退 + 本地模型 | **必须做回退链** |
| 跨域同步 | 应用层双写 | Kafka MirrorMaker | **Kafka (6个月后)** |
| 缓存 | 仅 Redis | 多级缓存 (L1+L2+L3) | **阶段 1 只用 Redis, 阶段 2 加 CDN** |
| 部署 | Docker Compose | K8s | **立即切 K8s (3个月)** |
| 分片 | 应用层分片 | 数据库中间件 | **应用层 (更灵活, 更可控)** |
| 多区域 | 主备 (Active-Passive) | 多活 (Active-Active) | **阶段 2 主备, 阶段 3 多活** |

### 8.3 降本增效建议

1. **预留实例**: 1 年预付节省 ~30%, 3 年预付节省 ~50%
2. **Spot 实例**: 无状态 Pod 跑在 Spot 上 (占 60%), 节省 ~60%
3. **分片均衡**: 监控热点分片, 自动 rebalance
4. **冷数据归档**: 超过 90 天的数据归档到廉价存储 (OSS 低频 / S3 Glacier)
5. **AI 缓存**: 相同名片 OCR 结果缓存, 避免重复调用 (缓存命中率预计 >40%)

---

## 9. 附录：关键代码模式

### 9.1 CrmAdapter 统一接口 (推荐新接口，标准化现有实现)

```python
# app/connectors/interfaces.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ContactData:
    external_id: str
    name: str
    email: str
    phone: str = ""
    company: str = ""
    title: str = ""
    department: str = ""
    tags: list[str] = field(default_factory=list)
    raw: dict | None = None

    def to_dict(self) -> dict:
        return {
            "external_id": self.external_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "company": self.company,
            "title": self.title,
            "department": self.department,
            "tags": self.tags,
            "raw": self.raw,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ContactData":
        return cls(**{k: d.get(k) for k in cls.__dataclass_fields__})


@dataclass
class SyncResult:
    success: bool
    created: int = 0
    updated: int = 0
    deleted: int = 0
    errors: list[str] = field(default_factory=list)
    details: str = ""


@dataclass
class WebhookEvent:
    provider: str
    event_type: str        # contact.created / contact.updated / contact.deleted
    contact: ContactData
    raw: dict


class CrmAdapter(ABC):
    """CRM 适配器统一抽象接口。"""

    @abstractmethod
    async def authenticate(self) -> bool: ...

    @abstractmethod
    async def get_contact(self, external_id: str) -> Optional[ContactData]: ...

    @abstractmethod
    async def search_contacts(self, query: str, limit: int = 20) -> list[ContactData]: ...

    @abstractmethod
    async def create_contact(self, contact: ContactData) -> SyncResult: ...

    @abstractmethod
    async def update_contact(self, contact: ContactData) -> SyncResult: ...

    @abstractmethod
    async def delete_contact(self, external_id: str) -> SyncResult: ...

    @abstractmethod
    async def sync_contacts(self, contacts: list[ContactData], strategy: str = "upsert") -> SyncResult: ...

    @abstractmethod
    async def health_check(self) -> dict: ...

    @abstractmethod
    async def webhook_verify(self, payload: dict) -> bool: ...

    @abstractmethod
    async def webhook_parse(self, payload: dict) -> WebhookEvent: ...

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def region(self) -> str: ...   # "overseas" | "china" | "self_hosted"
```

### 9.2 降级链执行器

```python
# app/services/crm_chain.py
import logging
from typing import Optional
from app.connectors.interfaces import CrmAdapter, ContactData, SyncResult

logger = logging.getLogger(__name__)


class CrmDegradationChain:
    """CRM 降级链 — 按优先级依次尝试，直到成功。"""

    def __init__(self, adapters: list[CrmAdapter]):
        self.adapters = adapters  # 按优先级从高到低排序

    async def execute_contact_sync(
        self, contact: ContactData
    ) -> tuple[SyncResult, Optional[str]]:
        """执行联系人与所有可用 CRM 的同步（第一个成功即止）。"""
        last_error = None
        for adapter in self.adapters:
            try:
                if not await adapter.authenticate():
                    logger.warning("CRM 认证失败: %s", adapter.provider_name)
                    continue

                result = await adapter.create_contact(contact)
                if result.success:
                    logger.info("CRM 同步成功: %s", adapter.provider_name)
                    return result, adapter.provider_name

                last_error = result.errors[0] if result.errors else "unknown error"
                logger.warning("CRM 同步失败: %s error=%s", adapter.provider_name, last_error)

            except Exception as e:
                last_error = str(e)
                logger.warning("CRM 异常: %s error=%s", adapter.provider_name, last_error)
                continue

        logger.error("所有 CRM 均不可达")
        return SyncResult(success=False, errors=[str(last_error)]), None

    async def health_check_all(self) -> dict[str, dict]:
        """检查所有适配器的健康状态。"""
        result = {}
        for adapter in self.adapters:
            try:
                result[adapter.provider_name] = {
                    **await adapter.health_check(),
                    "region": adapter.region,
                }
            except Exception as e:
                result[adapter.provider_name] = {"status": "error", "error": str(e)}
        return result
```

### 9.3 AI 服务多回退路由

```python
# app/ai/ai_router.py
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AIProvider:
    """单个 AI 提供商的包装器。"""
    def __init__(self, name: str, call_fn, region: str):
        self.name = name
        self.call_fn = call_fn
        self.region = region

    async def chat(self, messages: list[dict], **kwargs) -> dict:
        return await self.call_fn(messages, **kwargs)


class AIRouter:
    """AI 服务智能路由器 — 支持多提供商回退和地理感知。"""

    def __init__(self, user_region: str = "cn"):
        self.user_region = user_region
        self.providers = self._build_chain()

    def _build_chain(self) -> list[AIProvider]:
        from .providers import (
            deepseek, baidu_wenxin, ali_qwen,
            openai, anthropic, local_qwen
        )
        if self.user_region == "cn":
            return [
                AIProvider("deepseek", deepseek.chat, "cn"),
                AIProvider("baidu_wenxin", baidu_wenxin.chat, "cn"),
                AIProvider("ali_qwen", ali_qwen.chat, "cn"),
                AIProvider("local_qwen2.5-7b", local_qwen.chat, "cn"),
            ]
        else:
            return [
                AIProvider("openai", openai.chat, "us"),
                AIProvider("anthropic", anthropic.chat, "us"),
                AIProvider("deepseek_overseas", deepseek.chat, "us"),
                AIProvider("local_qwen2.5-7b", local_qwen.chat, "us"),
            ]

    async def chat(self, messages: list[dict], **kwargs) -> dict:
        last_error = None
        for provider in self.providers:
            try:
                result = await provider.chat(messages, **kwargs)
                logger.info("AI 路由成功: provider=%s region=%s",
                            provider.name, provider.region)
                return {"provider": provider.name, "data": result, "fallback": False}
            except Exception as e:
                last_error = e
                logger.warning("AI 路由失败: provider=%s error=%s",
                               provider.name, str(e))
                continue

        logger.error("所有 AI 提供商均不可达")
        return {
            "provider": None,
            "data": None,
            "fallback": True,
            "error": str(last_error),
        }
```

---

## 总结

```
AI 数智名片全球架构核心要点:

1. CRM 多态连接层:  8+ 适配器 + 自动发现 + 降级链 (海外→中国→自托管→缓存)
2. 1 亿用户扩展:    PostgreSQL 分片 + Redis 集群 + Kafka 跨域同步 + Kong 全球路由
3. 海外API容错:     DeepSeek→文心→通义→本地模型 / Salesforce→纷享销客→Supabase→缓存
4. 阶段式路线图:     现在(验证) → 3月(1万) → 6月(10万) → 12月(100万+) → 24月(1亿)
5. 成本控制:        预留实例 + Spot 混部 + 冷数据归档 + AI 缓存 + 按量弹性伸缩
```

---

> **文档维护者**: AI 数智名片架构组  
> **最后更新**: 2026-07-01  
> **下次评审**: 2026-10-01  
> **相关文档**: [ARCHITECTURE.md](../../ARCHITECTURE.md) · [OBSERVABILITY.md](../OBSERVABILITY.md) · [SECURITY.md](../../SECURITY.md) · [API_STANDARDS.md](../API_STANDARDS.md)
