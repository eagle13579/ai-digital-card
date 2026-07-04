# Rate Limit 客户端 SDK

## 概述

Rate Limit SDK 为链客宝内部微服务提供速率限制客户端封装。它直接操作进程内共享的 `TokenBucket` 存储（与 `middleware/rate_limit_middleware.py` 共享 `_IP_BUCKETS` 全局字典），支持同步和异步两种使用模式。

### 功能

| 函数 | 描述 |
|---|---|
| `check_rate_limit(key, limit, window)` | 检查指定 key 是否被限流，消费一个令牌 |
| `get_remaining(key)` | 查询指定 key 的剩余令牌数，不消费令牌 |
| `reset_bucket(key)` | 重置指定 key 的限流桶 |
| `get_all_buckets()` | 获取所有活跃的限流桶信息 |

### API 端点

| 方法 | 路径 | 描述 |
|---|---|---|
| GET | `/api/v1/rate-limit/status` | 当前所有限流桶状态（管理员） |
| GET | `/api/v1/rate-limit/remaining` | 当前请求的剩余次数 |

> **注意**: 上述端点已被 RateLimitMiddleware 加入白名单（`/api/v1/rate-limit/*`），不会被限流。

---

## 安装

SDK 位于 `backend/sdk/` 目录，与主项目代码一起部署，无需额外安装。

```bash
# 确保项目根目录在 Python 路径中
cd D:/chainke-full/backend
export PYTHONPATH=.:$PYTHONPATH   # Linux/Mac
set PYTHONPATH=.;%PYTHONPATH%     # Windows
```

---

## 同步客户端示例

```python
from sdk.rate_limit_client import RateLimitClient

# 创建客户端（可选自定义默认速率）
client = RateLimitClient(
    default_rate=60,   # 默认 60 请求/分钟
    auth_rate=10,      # 认证相关 10 请求/分钟
    admin_rate=120,    # 管理员 120 请求/分钟
)

# 检查限流
result = client.check_rate_limit(
    key="user:12345",
    limit=30,       # 可选，覆盖默认速率
    window=60,      # 时间窗口（秒）
)

if result["allowed"]:
    print(f"请求允许，剩余 {result['remaining']} 次")
else:
    print(f"已被限流，请在 {result['reset_time']} 后重试")

# 查询剩余（不消费令牌）
remaining = client.get_remaining("user:12345")
print(f"剩余请求数: {remaining}")

# 重置桶
client.reset_bucket("user:12345")

# 获取所有活跃桶
all_buckets = client.get_all_buckets()
for b in all_buckets:
    print(f"key={b['key']}, remaining={b['remaining']}, rate={b['rate']}")

# 当前活跃桶数量
count = client.active_bucket_count
```

---

## 异步客户端示例

```python
from sdk.rate_limit_client import AsyncRateLimitClient

async_client = AsyncRateLimitClient()

# 检查限流（异步）
result = await async_client.check_rate_limit(
    key="service:api-gateway",
    limit=100,
    window=60,
)

if result["allowed"]:
    print(f"允许请求，剩余 {result['remaining']} 次")

# 查询剩余
remaining = await async_client.get_remaining("service:api-gateway")

# 重置
await async_client.reset_bucket("service:api-gateway")

# 获取所有桶
buckets = await async_client.get_all_buckets()
```

---

## 模块级便捷函数

对于快速使用场景，SDK 提供了单例模式的模块级函数：

```python
from sdk.rate_limit_client import (
    check_rate_limit,
    get_remaining,
    reset_bucket,
    get_all_buckets,
)

# 无需手动创建客户端
result = check_rate_limit("my-key", limit=50, window=60)
remaining = get_remaining("my-key")
reset_bucket("my-key")
all_buckets = get_all_buckets()
```

---

## 在中间件中使用 SDK 端点确认白名单状态

Rate Limit SDK 的 REST 端点 (`/api/v1/rate-limit/*`) 已在 `RateLimitMiddleware` 中配置为白名单，不会被限流。你可以在代码中确认：

```python
from app.middleware.rate_limit_middleware import _is_whitelisted_path

assert _is_whitelisted_path("/api/v1/rate-limit/status") == True
assert _is_whitelisted_path("/api/v1/rate-limit/remaining") == True
assert _is_whitelisted_path("/api/v1/rate-limit/admin/cleanup") == True
```

---

## 配置说明

### 环境变量

| 变量 | 默认值 | 描述 |
|---|---|---|
| `RATE_LIMIT_DEFAULT` | `60` | 默认全局速率（请求/分钟/IP） |
| `RATE_LIMIT_AUTH` | `10` | 认证端点速率（请求/分钟/IP） |
| `RATE_LIMIT_ADMIN` | `120` | 管理端点速率（请求/分钟/IP） |

### 客户端构造参数

| 参数 | 默认值 | 描述 |
|---|---|---|
| `default_rate` | `60` | 默认速率 |
| `auth_rate` | `10` | 认证相关速率 |
| `admin_rate` | `120` | 管理员速率 |

---

## 返回值格式

### `check_rate_limit` 返回值

```json
{
    "allowed": true,
    "remaining": 9,
    "reset_time": 1700000000.0,
    "limit": 10,
    "window": 60
}
```

### `get_all_buckets` 返回值

```json
[
    {
        "key": "192.168.1.1",
        "rate": 60,
        "remaining": 45,
        "window": 60,
        "created_at": 1700000000.0
    }
]
```

---

## 常见问题

### Q: 为什么不支持 Redis/分布式？

当前版本直接操作进程内内存存储，与中间件共享 `_IP_BUCKETS` 字典。在单进程部署中这是最高效的方案。当需要多进程/多实例部署时，需要切换到 Redis 等集中式存储。届时 `RateLimitClient` 和 `AsyncRateLimitClient` 接口保持不变，只需修改底层存储实现。

### Q: 同步和异步客户端有什么区别？

目前功能完全相同（因为内存操作没有 I/O 阻塞），但异步客户端提供了 `async/await` 接口。当未来切换到 Redis 等异步驱动时，同步客户端代码无需变更，异步客户端也能无缝升级。

### Q: get_remaining 和 check_rate_limit 的区别？

- `check_rate_limit`: 消费一个令牌，返回是否允许继续。
- `get_remaining`: 仅查询剩余令牌数，**不消费令牌**。

### Q: 如何判断是否需要降级？

在发起重要请求前，先调用 `get_remaining(key)` 检查剩余次数。如果剩余不足 20%，可以考虑降级服务（如缓存响应、减少数据量）。

### Q: 并发安全吗？

是的。`TokenBucket.consume()` 和 `TokenBucket._refill()` 是线程安全的（仅涉及浮点数运算和赋值）。多个线程同时访问同一个 key 时不会出现数据竞争。详见测试用例 `test_concurrent_access`。

---

## 测试

```bash
# 运行所有 SDK 测试
cd D:/chainke-full/backend
pytest sdk/tests/ -v

# 仅运行同步客户端测试
pytest sdk/tests/ -v -k "TestRateLimitClient"

# 仅运行异步客户端测试
pytest sdk/tests/ -v -k "TestAsyncRateLimitClient"

# 仅运行并发测试
pytest sdk/tests/ -v -k "TestConcurrency"
```
