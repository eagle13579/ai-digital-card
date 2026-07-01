"""契约测试包 — HTTP 请求/响应格式一致性验证。

当前使用 pytest + httpx (ASGITransport) 实现轻量级契约检查。
未来可迁移至 Pact Python 框架实现消费者驱动契约。
"""
