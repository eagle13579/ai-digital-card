# AI数字名片 契约测试规范

> 版本: 1.0 · 最后更新: 2026-07-01

---

## 1. 概述

契约测试 (Contract Testing) 确保 **服务提供方 (Provider)** 与 **服务消费方 (Consumer)** 之间的 API 交互协议始终一致。  
本规范定义了 AI数字名片 项目的契约测试体系，所有新 API 端点必须附带对应的契约测试。

---

## 2. 三种测试的职责边界

| 维度 | 单元测试 (Unit) | 契约测试 (Contract) | 集成测试 (Integration) |
|------|----------------|---------------------|----------------------|
| **范围** | 单个函数/方法 | 两个系统之间的 API 接口 | 跨多个真实组件的流程 |
| **关注点** | 业务逻辑正确性 | 请求/响应格式一致性 | 端到端功能完整性 |
| **外部依赖** | Mock / Stub | 真实 HTTP 请求 (或 ASGI Transport) | 真实数据库 / 第三方服务 |
| **运行速度** | 毫秒级 | 亚秒级 | 秒~分钟级 |
| **失败含义** | 逻辑 bug | 协议不兼容 | 组件配合断裂 |
| **触发时机** | 每次提交 | 每次提交 + PR | 合并前 / 定时 |

### 2.1 原则

- **契约测试不是集成测试的替代品**，两者互补。
- **契约测试定位在单元测试与集成测试之间**：比单元测试更贴近真实 HTTP 层，但比集成测试更轻量、更聚焦。
- **契约测试只验证"格式"，不验证"业务结果"**。

---

## 3. 推荐框架: Pact (消费者驱动契约)

> 当前阶段使用 `pytest + httpx` (ASGITransport) 实现 HTTP 级契约检查，未来可迁移到 [Pact Python](https://pact.readthedocs.io/) 实现消费者驱动契约。

### 3.1 httpx (当前) vs Pact (未来)

| 特性 | httpx (当前) | Pact (未来) |
|------|-------------|-------------|
| 学习成本 | 低 (复用已有工具栈) | 中 (需学习 Pact DSL) |
| 协议强校验 | 手动断言 | 自动匹配 |
| 消费者驱动 | ❌ | ✅ |
| Broker / CI 集成 | ❌ | ✅ |
| 适合阶段 | Phase 1 快速落地 | Phase 2 规模化 |

---

## 4. 契约定义模板

### 4.1 端点契约格式

每个 API 端点的契约应定义三部分：

```python
ENDPOINT_CONTRACT = {
    "method": "GET",
    "path": "/api/users/me",
    "auth_required": True,
    "request": {
        "headers": {"Authorization": "Bearer <token>"},
        "query_params": {},
        "body": None,
    },
    "response": {
        "200": {
            "schema": {
                "type": "object",
                "required_fields": ["id", "phone", "name"],
                "field_types": {"id": int, "phone": str},
            },
            "headers": {"content-type": "application/json"},
        },
        "401": {"description": "未认证", "schema": {"required_fields": ["detail"]}},
        "404": {"description": "资源不存在", "schema": {"required_fields": ["detail"]}},
        "422": {"description": "参数校验失败", "schema": {"required_fields": ["detail"]}},
    },
}
```

### 4.2 通用合约 (所有端点必须遵守)

| 规则 | 说明 |
|------|------|
| 内容类型 | 成功响应必须是 `application/json` (除 `/health`) |
| 错误格式 | 所有错误响应必须包含 `detail` 字段 (字符串) |
| 认证失败 | 未提供/无效 token 返回 `401` |
| 资源不存在 | `404` + 描述性错误信息 |
| 参数校验失败 | `422` + 详细校验错误 |

---

## 5. 目录结构与命名规范

```
backend/tests/
├── contracts/
│   ├── __init__.py
│   ├── conftest.py              # 契约测试基础配置与 fixture
│   ├── test_user_contract.py    # 用户 API 契约
│   ├── test_brochure_contract.py
│   └── test_auth_contract.py
├── conftest.py                  # 全局测试配置
├── test_api.py                  # 集成测试
└── test_contract_api.py         # (旧) 后续迁移至此目录
```

### 命名规则

- 文件名: `test_{模块}_contract.py`
- 类名: `Test{模块}Contract`
- 方法名: `test_{场景}_contract`

---

## 6. 契约测试编写规范

### 6.1 基础结构

```python
class TestUserContract:
    def test_get_me_contract(self, client, auth_headers):
        resp = client.get("/api/users/me", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        required = {"id", "phone", "name", "avatar", "company", "title",
                     "intro", "role", "membership_tier", "created_at", "updated_at"}
        assert required.issubset(data.keys())
        assert isinstance(data["id"], int)
```

### 6.2 必须覆盖的场景

| 场景 | 验证内容 |
|------|---------|
| ✅ 成功响应 | 状态码 + Content-Type + 必选字段 + 字段类型 |
| ❌ 未认证 (401) | 请求未携带 token 时的错误格式 |
| ❌ 资源不存在 (404) | 请求不存在的资源时的错误格式 |
| ❌ 参数校验失败 (422) | 请求参数不符合 schema 时的错误格式 |
| ❌ 业务冲突 (400) | 重复注册等业务约束冲突时的错误格式 |

### 6.3 禁止行为

- ❌ 不验证业务逻辑 (如权限判断、计算逻辑)
- ❌ 不依赖外部服务 (直接 mock 或替换依赖)
- ❌ 不做数据清理 (使用隔离的 in-memory 数据库)
- ✅ 只验证: 状态码、Content-Type、字段存在性、字段类型

---

## 7. CI 集成方案

### 7.1 GitHub Actions

```yaml
name: Contract Tests
on:
  push: {branches: [main, develop]}
  pull_request: {branches: [main]}
jobs:
  contract:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.12"}
      - name: Install
        run: pip install -r requirements_full.txt pytest pytest-asyncio httpx
      - name: Run contract tests
        run: cd backend && pytest tests/contracts/ -v --tb=short
```

### 7.2 运行方式

```bash
# 只跑契约测试
pytest tests/contracts/ -v
# 跳过契约测试
pytest tests/ -v --ignore=tests/contracts
# 混合跑 + 覆盖率
pytest tests/contracts/ tests/test_api.py -v --cov=app
```

### 7.3 PR 检查清单

```markdown
## 契约检查
- [ ] 新增/修改的 API 端点已添加契约测试
- [ ] 契约测试覆盖了成功和所有错误场景
- [ ] 契约测试不依赖外部服务
```

---

## 8. 迁移计划

| 阶段 | 内容 | 时间 |
|------|------|------|
| Phase 1 | ✅ 创建契约测试目录与规范 | 当前 |
| Phase 2 | 🔄 将 `test_contract_api.py` 重构到 `contracts/` 目录 | 本周 |
| Phase 3 | 🔲 为所有 42 个端点添加契约测试 | 本迭代 |
| Phase 4 | 🔲 引入 Pact 框架 + Broker | 下迭代 |

---

## 9. 参考

- [Pact Python 文档](https://pact.readthedocs.io/)
- [Martin Fowler — ContractTest](https://martinfowler.com/bliki/ContractTest.html)
- [OpenAPI 规范](https://spec.openapis.org/oas/v3.0.3)
