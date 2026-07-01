"""
缓存层单元测试 — @cache / invalidate / cached_property / init_cache。

覆盖 10 个测试用例:
  1. @cache get/set 命中
  2. 不同参数独立缓存
  3. TTL 过期重新计算
  4. skip_none 跳过 None
  5. 自定义 prefix
  6. clear_cache 手动清除
  7. Redis 不可用降级
  8. invalidate 按前缀失效
  9. cached_property 双层缓存
  10. init_cache 成功/失败
"""

import json
import time
from unittest.mock import MagicMock, patch, AsyncMock

import pytest


class _FakeRedis:
    """伪 Redis 客户端，模拟 RedisClient 核心方法。"""
    def __init__(self):
        self._store = {}
        self._ttl = {}

    def _serialize(self, v):
        return json.dumps(v, ensure_ascii=False, default=str).encode()
    def _deserialize(self, d):
        if d is None:
            return None
        return json.loads(d.decode())

    def get(self, key):
        raw = self._store.get(key)
        if raw is None:
            return None
        expiry = self._ttl.get(key)
        if expiry and time.time() > expiry:
            self._store.pop(key, None)
            self._ttl.pop(key, None)
            return None
        return self._deserialize(raw)

    def set(self, key, value, ttl=None):
        self._store[key] = self._serialize(value)
        if ttl:
            self._ttl[key] = time.time() + ttl

    def delete(self, key):
        self._store.pop(key, None)
        self._ttl.pop(key, None)
        return 1

    def exists(self, key):
        return key in self._store

    def scan_keys(self, pattern):
        import fnmatch
        return [k for k in self._store if fnmatch.fnmatch(k, pattern)]

    @property
    def client(self):
        return self

    def ping(self):
        return True

    def pipeline(self):
        return _FakePipe(self._store, self._ttl)


class _FakePipe:
    def __init__(self, store, ttl):
        self.store = store
        self.ttl = ttl
        self.cmds = []

    def delete(self, k):
        self.cmds.append(k)
        return self

    def execute(self):
        for k in self.cmds:
            self.store.pop(k, None)
            self.ttl.pop(k, None)
        return [1] * len(self.cmds)


@pytest.fixture
def fake_redis():
    fr = _FakeRedis()
    with patch("app.cache.redis._redis_client", fr), \
         patch("app.cache._get_client", return_value=fr):
        yield fr


@pytest.fixture
def no_redis():
    with patch("app.cache.redis._redis_client", None), \
         patch("app.cache._get_client", return_value=None):
        yield


# ── @cache 装饰器 (7 用例) ──────────────────────────────────────────


class TestCacheDecorator:
    def test_get_set(self, fake_redis):
        from app.cache import cache
        cnt = 0
        @cache(ttl=60)
        def f(k):
            nonlocal cnt; cnt += 1
            return {"v": k}
        assert f("a") == {"v": "a"}; assert cnt == 1
        assert f("a") == {"v": "a"}; assert cnt == 1  # 命中

    def test_different_args(self, fake_redis):
        from app.cache import cache
        cnt = 0
        @cache(ttl=60)
        def f(n):
            nonlocal cnt; cnt += 1
            return n * 2
        assert f(1) == 2; assert f(2) == 4; assert cnt == 2

    def test_expiry(self, fake_redis):
        from app.cache import cache
        cnt = 0
        @cache(ttl=1)
        def f():
            nonlocal cnt; cnt += 1
            return cnt
        assert f() == 1
        assert f() == 1  # 命中
        time.sleep(1.1)
        assert f() == 2  # 过期重新执行

    def test_skip_none(self, fake_redis):
        from app.cache import cache
        cnt = 0
        @cache(ttl=60, skip_none=True)
        def f(ok):
            nonlocal cnt; cnt += 1
            return ok if None else None
        assert f(False) is None; c1 = cnt
        assert f(False) is None; assert cnt == c1 + 1  # None 不缓存

    def test_custom_prefix(self, fake_redis):
        from app.cache import cache
        @cache(ttl=60, prefix="my_pfx")
        def f():
            return 1
        f()
        assert fake_redis.scan_keys("my_pfx:*")

    def test_clear_cache(self, fake_redis):
        from app.cache import cache
        @cache(ttl=60)
        def f(k):
            return k
        f("x")
        assert fake_redis.scan_keys(f"{f.cache_prefix}:*")
        f.clear_cache("x")
        assert not fake_redis.scan_keys(f"{f.cache_prefix}:*")

    def test_no_redis_graceful(self, no_redis):
        from app.cache import cache
        cnt = 0
        @cache(ttl=60)
        def f():
            nonlocal cnt; cnt += 1
            return cnt
        assert f() == 1
        assert f() == 2  # 无 Redis 不缓存


# ── invalidate (1 用例) ────────────────────────────────────────────


class TestInvalidate:
    def test_by_prefix(self, fake_redis):
        from app.cache import invalidate
        fake_redis.set("m:1:2:a", 1)
        fake_redis.set("m:1:2:b", 2)
        fake_redis.set("m:1:3:c", 3)
        assert invalidate("m", 1, 2) == 2
        assert not fake_redis.exists("m:1:2:a")
        assert fake_redis.exists("m:1:3:c")


# ── cached_property (1 用例) ───────────────────────────────────────


class TestCachedProperty:
    def test_basic(self, fake_redis):
        from app.cache import cached_property
        class C:
            cnt = 0
            @cached_property(ttl=60)
            def val(self):
                self.cnt += 1
                return self.cnt
        c = C()
        assert c.val == 1
        assert c.val == 1  # 本地缓存命中
        assert c.cnt == 1


# ── init_cache (1 用例) ────────────────────────────────────────────


class TestInitCache:
    def test_success_and_failure(self):
        from app.cache import init_cache
        from app.cache.redis import RedisClient
        # 成功
        with patch.object(RedisClient, "__init__", return_value=None), \
             patch.object(RedisClient, "ping", return_value=True):
            assert init_cache(redis_host="localhost") is not None
        # 失败
        with patch.object(RedisClient, "__init__", side_effect=Exception("fail")):
            assert init_cache(redis_host="bad") is None
