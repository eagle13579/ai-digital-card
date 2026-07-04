# 链客宝缓存策略文档

## 概述

本文档定义链客宝后端项目的缓存策略，包括哪些数据适合缓存、TTL 配置建议、
失效策略、以及缓存穿透/雪崩/击穿的防护方案。

---

## 1. 缓存策略总览

| 层级 | 后端 | 用途 | 适用场景 |
|------|------|------|----------|
| L1 | LocalCache (内存) | 超低延迟读取、Redis 降级 | 热点小数据、Redis 不可用时的保底 |
| L2 | Redis | 分布式缓存、TTL 管理 | 所有可缓存数据的主存储 |

架构原则：
- **写穿透（Write-Through）**：写入时同时更新 Redis 和 LocalCache
- **惰性过期（Lazy Expiration）**：读取时检查 TTL，过期即失效
- **先 Redis 后 Local**：读取时优先查 Redis，未命中回查 LocalCache

---

## 2. 什么数据适合缓存

### ✅ 适合缓存的数据

| 数据类型 | 示例 Key | TTL 建议 | 说明 |
|---------|----------|----------|------|
| **用户基本信息** | `user:{id}` | 600s (10min) | 低频变化，高频读取 |
| **商品/产品信息** | `product:{id}` | 300s (5min) | 商家后台更新后可手动失效 |
| **配置/字典数据** | `config:{key}` | 3600s (1h) | 极少变化 |
| **静态列表** | `categories` | 3600s (1h) | 分类、标签等低频变化数据 |
| **热门排行榜** | `ranking:{type}` | 120s (2min) | 实时性要求不高 |
| **SEO 结构化数据** | `seo:jsonld:{path}` | 86400s (24h) | 静态化输出 |
| **i18n 翻译** | `i18n:{lang}:{key}` | 86400s (24h) | 翻译部署时才变化 |
| **计数/统计** | `stats:{metric}` | 60s (1min) | 允许最终一致性 |
| **API 响应片段** | `api:{method}:{path}` | 60-300s | GET 幂等响应，详见中间件 |

### ❌ 不适合缓存的数据

- **用户会话/Token** — 使用专门的 Session Store 或 JWT
- **支付状态/订单状态** — 需要强一致性，直接查数据库
- **实时消息/通知** — 使用消息队列
- **验证码** — 使用专门的存储（TTL 极短，与缓存逻辑分离）
- **包含敏感信息的响应** — 如包含用户手机号、身份证等

---

## 3. TTL 配置规范

### 3.1 通用原则

```
TTL = 数据平均变更间隔 × 0.8
```

即 TTL 设定为数据预期变更周期的 80%，确保大部分时间缓存有效。

### 3.2 TTL 分级

| 级别 | 范围 | 适用场景 |
|------|------|---------|
| **极短** | 1s - 30s | 计数器、实时排名 |
| **短** | 60s - 300s | API 响应、商品信息 |
| **中** | 300s - 1800s | 用户信息、配置 |
| **长** | 1800s - 86400s | 静态字典、SEO数据 |
| **永久** | 无过期 | 极少（需手动失效机制） |

### 3.3 环境差异化

```python
# 开发环境使用短 TTL 便于调试
TTL_MULTIPLIER = {
    "development": 0.1,   # 正常 TTL × 0.1
    "testing": 0.3,
    "production": 1.0,
}
```

---

## 4. 缓存 Key 命名规范

### 4.1 命名格式

```
{prefix}:{domain}:{identifier}[:{sub}]
```

- **prefix**: `chainke`（由 `REDIS_PREFIX` 环境变量定义）
- **domain**: 业务域，如 `user`, `product`, `config`, `api`
- **identifier**: 具体标识，如 ID、slug、路径
- **sub**: （可选）子标识

### 4.2 示例

```
chainke:user:42
chainke:product:sku_12345
chainke:config:site_title
chainke:api:GET:/api/brochure/42
chainke:seo:jsonld:/products/abc
chainke:stats:daily_active_users
```

### 4.3 禁止项

- ❌ 不要使用动态增长的无界 Key（如 `user:1`, `user:2` ... 无限递增）
- ❌ 不要在 Key 中包含敏感信息（用户密码、手机号）
- ❌ 不要使用空格、中文等非 ASCII 字符

---

## 5. 失效策略

### 5.1 自动失效（TTL 到期）

由 Redis 自动删除过期键，无需人工干预。

### 5.2 主动失效（写操作触发）

当数据发生变更时，业务代码应主动删除或更新缓存。

```python
# 更新用户信息后失效缓存
from app.cache import cache
await cache.delete(f"user:{user_id}")

# 或者直接更新
updated_user = await update_user_in_db(user_id, data)
await cache.set(f"user:{user_id}", updated_user.to_dict(), ttl=600)
```

### 5.3 批量失效（Pattern 匹配）

```python
# 清除某个域下所有缓存
keys = await cache._redis.keys("user:*")
for key in keys:
    await cache._redis.redis.delete(key)  # 底层操作，谨慎使用
```

> **⚠️ 生产环境禁止直接使用 `keys *`**。如有批量清理需求，可使用 Redis SCAN 命令或维护失效清单。

### 5.4 缓存更新模式

推荐 **Cache-Aside**（延迟加载）模式：

```
1. 读取: 查缓存 → 命中返回 → 未命中查 DB → 写入缓存 → 返回
2. 写入: 更新 DB → 删除缓存（而非更新缓存）
```

---

## 6. 缓存穿透防护

### 什么是缓存穿透

请求查询一个**根本不存在**的数据（如不存在的用户 ID），导致每次请求都穿透到数据库。

### 防护方案

#### 方案一：空值缓存（推荐）

```python
# 查询不存在的数据时，缓存空值（短 TTL）
value = await cache.get(key)
if value is None:
    data = await query_db(key)
    if data is None:
        # 缓存空值，TTL 设为 60s 防止长时间占用
        await cache.set(key, None, ttl=60)
        return None
    await cache.set(key, data)
    return data
return value
```

#### 方案二：布隆过滤器（大规模场景）

```python
# 初始化布隆过滤器
from redis_bloom import BloomFilter
bloom = BloomFilter(redis_conn, "chainke:bloom:user_ids")

# 写入时加入过滤器
bloom.add(user_id)

# 查询前先检查
if not bloom.exists(query_id):
    return None  # 一定不存在，无需查 DB
```

> 布隆过滤器适用于用户 ID、商品 ID 等**有限且可枚举**的场景，
> 当前项目规模暂不需要，将来用户量 > 100 万时可引入。

#### 方案三：参数校验

```python
# 在路由层拦截明显无效的参数
@router.get("/api/user/{user_id}")
async def get_user(user_id: int):
    if user_id <= 0 or user_id > MAX_VALID_ID:
        return JSONResponse(status_code=400, content={"error": "无效的用户ID"})
    # ... 后续查询
```

---

## 7. 缓存击穿防护

### 什么是缓存击穿

某个**热点 Key** 在过期瞬间，大量并发请求同时涌入，全部穿透到数据库。

### 防护方案

#### 方案一：互斥锁（推荐，`get_or_set` 已内置）

```python
from app.cache import cache

# 使用内置的 get_or_set 方法
# 底层通过分布式锁保证只有一个请求去加载数据
data = await cache.get_or_set(
    key="hot_product:123",
    factory=lambda: load_product_from_db(123),
    ttl=300,
)
```

#### 方案二：逻辑过期（热点数据不过期）

```python
# 缓存永不过期，但内部存储逻辑过期时间
cached_data = {
    "data": {...},
    "expire_at": current_timestamp + 3600,
}

# 后台线程异步刷新
if cached_data["expire_at"] < now:
    # 立即返回旧数据 + 异步更新
    asyncio.create_task(refresh_cache(key))
    return cached_data["data"]
```

#### 方案三：预热（启动时加载热点数据）

```python
# 应用启动时预加载热门数据
async def warm_up_cache():
    hot_products = await db.query("SELECT * FROM products WHERE is_hot = 1")
    for product in hot_products:
        await cache.set(f"product:{product.id}", product.to_dict())
```

---

## 8. 缓存雪崩防护

### 什么是缓存雪崩

大量缓存集中在同一时间过期，或 Redis 服务宕机，导致所有请求直达数据库。

### 防护方案

#### 方案一：TTL 随机化

```python
import random

# 设置 TTL 时加入随机偏移，避免批量同时过期
ttl = BASE_TTL + random.randint(-60, 60)
await cache.set(key, value, ttl=ttl)
```

#### 方案二：本地缓存降级（已内置）

```python
# 当 Redis 不可用时自动降级到 LocalCache
# 由 cache.py 的 Cache 类自动处理
# 无需业务代码改动
```

#### 方案三：限流熔断

在数据库访问层加入限流保护。

```python
# 使用 asyncio.Semaphore 控制并发查询数
db_semaphore = asyncio.Semaphore(10)

async def limited_db_query(query):
    async with db_semaphore:
        return await db.execute(query)
```

#### 方案四：多级缓存

```
本地缓存 (LocalCache) → Redis → 数据库
                    ↕
             命中即返回，逐级回退
```

#### 方案五：Redis 高可用

- 生产环境部署 Redis Sentinel 或 Redis Cluster
- 配置 `docker-compose.redis.yml` 时建议使用主从模式

---

## 9. 监控与告警

### 关键指标

| 指标 | 说明 | 告警阈值 |
|------|------|---------|
| `cache_hit_rate` | 缓存命中率 | < 80% 告警 |
| `cache_misses_total` | 未命中次数 | 突增 5 倍告警 |
| `redis_connected` | Redis 连接状态 | 断开立即告警 |
| `redis_memory_usage` | Redis 内存使用 | > 80% 告警 |
| `slow_query_rate` | 穿透到 DB 的请求率 | > 10% 告警 |

### 查看实时统计

```python
from app.cache import cache

# 程序内获取
stats = cache.stats()
print(stats.to_dict())

# 日志输出
logger.info(cache.stats_report())
```

---

## 10. 最佳实践清单

- [x] 所有缓存操作通过 `from app.cache import cache` 统一接口
- [x] 写操作先更新数据库，再删除缓存（Cache-Aside）
- [x] 读操作用 `get_or_set` 防止缓存击穿
- [x] TTL 加入随机偏移防止雪崩
- [x] Redis 不可用时自动降级到本地缓存
- [x] 缓存 Key 统一使用冒号分隔的命名空间
- [x] 禁止缓存包含敏感信息
- [x] 使用 `CACHE_DISABLE=1` 在开发调试时绕过缓存

---

## 附录：快速参考

### 常用操作

```python
from app.cache import cache

# 简单读写
await cache.set("key", {"value": 42})
data = await cache.get("key", default={})

# 带 TTL
await cache.set("key", data, ttl=60)

# 缓存穿透防护
data = await cache.get_or_set("key", fetch_from_db, ttl=300)

# 删除
await cache.delete("key")

# 存在性检查
if await cache.exists("key"):
    ...

# 统计
print(cache.stats_report())

# 重置统计
cache.reset_stats()
```

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接地址 |
| `REDIS_TTL` | `300` | 默认缓存 TTL（秒） |
| `REDIS_PREFIX` | `chainke:` | 键前缀 |
| `CACHE_DISABLE` | `0` | 设为 `1` 禁用所有缓存 |
