"""
增强缓存测试 — @cache 装饰器 + invalidate + redis 客户端
覆盖 12+ 个测试用例（≤200行）
"""
import json, time, pytest
from unittest.mock import patch


class _FakeRedis:
    def __init__(self):
        self._store = {}
        self._ttl = {}

    def _deserialize(self, d):
        return None if d is None else json.loads(d.decode())

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
        self._store[key] = json.dumps(value, ensure_ascii=False, default=str).encode()
        if ttl:
            self._ttl[key] = time.time() + ttl

    def delete(self, key):
        return bool(self._store.pop(key, None))

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
        return _FakePipe(self._store)


class _FakePipe:
    def __init__(self, store):
        self.store = store
        self.cmds = []

    def delete(self, k):
        self.cmds.append(k)
        return self

    def execute(self):
        for k in self.cmds:
            self.store.pop(k, None)
        return [1] * len(self.cmds)


@pytest.fixture
def fake_redis():
    fr = _FakeRedis()
    with patch("app.cache.redis._redis_client", fr), \
         patch("app.cache._get_client", return_value=fr):
        yield fr


class TestCacheDecorator:
    def test_hit_returns_cached(self, fake_redis):
        from app.cache import cache
        calls = 0
        @cache(ttl=60)
        def f(k):
            nonlocal calls; calls += 1
            return {"v": k}
        assert f("a") == {"v": "a"}; assert calls == 1
        assert f("a") == {"v": "a"}; assert calls == 1

    def test_different_args_independent(self, fake_redis):
        from app.cache import cache
        calls = 0
        @cache(ttl=60)
        def f(n):
            nonlocal calls; calls += 1
            return n * 2
        assert f(1) == 2; assert f(2) == 4; assert calls == 2

    def test_ttl_expiry(self, fake_redis):
        from app.cache import cache
        calls = 0
        @cache(ttl=1)
        def f():
            nonlocal calls; calls += 1
            return calls
        assert f() == 1
        assert f() == 1
        time.sleep(1.1)
        assert f() == 2

    def test_skip_none(self, fake_redis):
        from app.cache import cache
        calls = 0
        @cache(ttl=60, skip_none=True)
        def f(v):
            nonlocal calls; calls += 1
            return v if v else None
        assert f(False) is None
        c1 = calls
        assert f(False) is None
        assert calls == c1 + 1

    def test_custom_prefix(self, fake_redis):
        from app.cache import cache
        @cache(ttl=60, prefix="my_pfx")
        def f():
            return 1
        f()
        assert fake_redis.scan_keys("my_pfx:*")

    def test_no_redis_graceful(self):
        with patch("app.cache.redis._redis_client", None), \
             patch("app.cache._get_client", return_value=None):
            from app.cache import cache
            calls = 0
            @cache(ttl=60)
            def f():
                nonlocal calls; calls += 1
                return calls
            assert f() == 1
            assert f() == 2

    @pytest.mark.asyncio
    async def test_async_cache_hit_and_miss(self, fake_redis):
        from app.cache import cache
        calls = 0
        @cache(ttl=60)
        async def af(x):
            nonlocal calls; calls += 1
            return x * 2
        coro = af(5)
        assert hasattr(coro, "__await__")
        assert await coro == 10 and calls == 1
        assert af(5) == 10 and calls == 1


class TestInvalidate:
    def test_by_prefix(self, fake_redis):
        from app.cache import invalidate
        fake_redis._store["m:1:2::a"] = b"1"
        fake_redis._store["m:1:2::b"] = b"2"
        fake_redis._store["m:1:3::c"] = b"3"
        assert invalidate("m", 1, 2) == 2
        assert not fake_redis.exists("m:1:2::a")
        assert fake_redis.exists("m:1:3::c")

    def test_invalidate_on_empty_store(self, fake_redis):
        from app.cache import invalidate
        assert invalidate("nonexistent", 1) == 0

    def test_empty_prefix_returns_zero(self, fake_redis):
        from app.cache import invalidate
        assert invalidate() == 0

    def test_no_redis_returns_zero(self):
        with patch("app.cache._get_client", return_value=None):
            from app.cache import invalidate
            assert invalidate("x") == 0


class TestRedisClient:
    def test_serialize_deserialize_roundtrip(self):
        from app.cache.redis import RedisClient
        data = {"hello": "world", "num": 42}
        assert RedisClient._deserialize(RedisClient._serialize(data)) == data

    def test_make_key(self):
        from app.cache.redis import RedisClient
        assert RedisClient.make_key("match", 1, 2) == "match:1:2"
        assert RedisClient.make_key("x", "a", suffix="s") == "x:a:s"

    def test_init_redis_failure_returns_none(self):
        from app.cache.redis import init_redis
        with patch("app.cache.redis.RedisClient", side_effect=Exception("fail")):
            assert init_redis(host="bad") is None
