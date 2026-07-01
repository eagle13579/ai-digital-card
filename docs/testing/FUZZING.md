# AI数字名片 Fuzzing测试规范

> 版本: 1.0 · 最后更新: 2026-07-01

---

## 1. 概述

Fuzzing测试（模糊测试）通过向系统注入随机、异常或极端的输入，验证 API 在非预期数据下不会崩溃（不返回 500），并返回合理的错误码。

### 1.1 目标

- **健壮性验证**: 确保超长字符串、特殊字符、Unicode、SQL注入、XSS等不导致服务端崩溃
- **安全边界**: 验证认证/授权体系不会被畸形输入绕过
- **输入验证**: 确认每个端点对无效输入的拒绝是优雅的（400/422/401/404），而不是抛异常

### 1.2 Fuzzing vs 其他测试

| 维度 | 单元测试 | 契约测试 | **Fuzzing测试** |
|------|---------|---------|-----------------|
| **输入** | 正常/边界值 | 正常 | **随机/极端/恶意** |
| **关注点** | 逻辑正确 | 协议一致性 | **防崩溃、防注入** |
| **输出验证** | 精确值 | 字段存在性 | **不返回500** |
| **运行频率** | 每次提交 | 每次提交 | 每次提交 + nightly |

---

## 2. Fuzzing策略

### 2.1 输入类型

所有 Fuzzing 测试使用以下输入类型生成变异 payload：

| # | 类型 | 示例 |
|---|------|------|
| 1 | **超长字符串** | 10KB~50KB 随机 ASCII |
| 2 | **特殊字符** | null字节(`\x00`), 控制字符(`\x01-\x1f`), shell转义(`'; rm -rf /;'`) |
| 3 | **Unicode/多字节** | CJK、Emoji (U+1F600+)、RTL、组合变音符号、零宽连接符 |
| 4 | **SQL注入** | `' OR '1'='1`, `'; DROP TABLE --` 等 10+ 种变体 |
| 5 | **XSS注入** | `<script>alert(1)</script>`, `<img src=x onerror=alert(1)>` 等 |
| 6 | **边界数值** | -1, 0, 2^31, 2^63-1, NaN, Infinity, 10^1000 |
| 7 | **空/缺失/null** | 空字符串 `""`, null 值, 删除关键字段 |
| 8 | **类型混淆** | 字符串当数字, 列表当字典, 整数当字符串 |
| 9 | **深层嵌套JSON** | 50层嵌套, 1000个字段的对象 |
| 10 | **畸形Token** | 超长 Bearer token, XSS token, SQL注入 token |

### 2.2 测试端点

核心 Fuzzing 覆盖的端点（共 16 个）：

| 端点 | 方法 | 认证要求 |
|------|------|---------|
| `/health` | GET | 无 |
| `/api/health` | GET | 无 |
| `/api/auth/register` | POST | 无 |
| `/api/auth/login` | POST | 无 |
| `/api/users/me` | GET | 需要 |
| `/api/users/me` | PUT | 需要 |
| `/api/tags/me` | GET | 需要 |
| `/api/tags/me` | POST | 需要 |
| `/api/tags/me/{id}` | DELETE | 需要 |
| `/api/brochures` | GET | 需要 |
| `/api/brochures` | POST | 需要 |
| `/api/brochures/{id}` | GET | 需要 |
| `/api/brochures/{id}` | DELETE | 需要 |
| `/api/trust/network` | GET | 需要 |
| `/api/trust/network` | POST | 需要 |

### 2.3 验证规则

对于每个 Fuzzing payload，必须验证：

```
✅ 允许的状态码: 200, 201, 400, 401, 403, 404, 422
❌ 禁止的状态码: 500 (Internal Server Error)
❌ 禁止的行为: 崩溃/超时/连接断开
```

---

## 3. 文件结构与命名

```
backend/tests/
├── fuzzing/
│   ├── __init__.py
│   └── test_api_fuzzing.py    # API Fuzzing 测试
├── conftest.py
└── ...
```

### 3.1 命名规则

- **文件**: `test_api_fuzzing.py`
- **类名**: `TestAPIFuzzing`, `TestFuzzingAdversarialScenarios`, `TestFuzzInfrastructure`
- **方法**: `test_fuzz_no_crash`, `test_sql_injection_no_crash`, `test_xss_injection_no_crash`
- **Marker**: 所有 Fuzzing 测试标记为 `@pytest.mark.fuzzing`

---

## 4. 测试分类

### 4.1 随机Fuzzing（TestAPIFuzzing）

对每个核心端点，使用 `_payload_variations()` 自动生成所有类型的变异 payload（每个字段逐一替换为超长字符串、特殊字符、Unicode、SQL注入、XSS、null、缺失、类型混淆等），并发起请求验证无崩溃。

- **输入**: 自动从 `SAMPLE_BODIES` 和 `FUZZ_ENDPOINTS` 生成
- **验证**: 每个 payload 请求后断言不返回 500
- **粒度**: 每个 endpoint 一个测试方法，parametrize 所有 payload

### 4.2 定向攻击场景（TestFuzzingAdversarialScenarios）

针对特定攻击向量的精细测试：

| 测试 | 描述 |
|------|------|
| `test_sql_injection_no_crash` | SQL注入payload × 4个端点 |
| `test_xss_injection_no_crash` | XSS payload × 3个端点 |
| `test_unicode_boundary_no_crash` | 万级Unicode字符 |
| `test_fuzzed_auth_tokens` | 畸形Bearer token |
| `test_path_injection_no_crash` | 路径遍历/注入 |
| `test_fuzzed_headers_no_crash` | 畸形HTTP头 |
| `test_fuzzed_query_params_no_crash` | 畸形查询参数 |
| `test_content_type_mismatch` | Content-Type不匹配 |
| `test_json_structure_bombs` | JSON结构炸弹 |

### 4.3 基础设施测试（TestFuzzInfrastructure）

验证 Fuzzing 辅助函数本身正常工作（生成器长度、variation 数量等）。

---

## 5. 运行方式

```bash
# 只跑 Fuzzing 测试
cd backend && pytest tests/fuzzing/ -v --tb=short -m fuzzing

# Fuzzing + 覆盖率
cd backend && pytest tests/fuzzing/ -v --cov=app --cov-report=term-missing

# 跳过 Fuzzing 测试（常规运行）
cd backend && pytest tests/ -v --ignore=tests/fuzzing

# 快速子集（只跑基础设施自检）
cd backend && pytest tests/fuzzing/ -v -k "infrastructure"
```

---

## 6. CI 集成

### 6.1 GitHub Actions

```yaml
name: Fuzzing Tests
on:
  push: {branches: [main, develop]}
  pull_request: {branches: [main]}
  schedule:
    - cron: "0 6 * * *"  # 每天 UTC 6:00 跑一次完整 Fuzzing
jobs:
  fuzzing:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.12"}
      - name: Install
        run: pip install -r requirements_full.txt pytest pytest-asyncio httpx
      - name: Run fuzzing tests
        run: cd backend && pytest tests/fuzzing/ -v --tb=short -m fuzzing --timeout=60
```

### 6.2 PR 检查清单

```markdown
## Fuzzing 检查
- [ ] Fuzzing 测试通过（不返回 500）
- [ ] 新端点已添加到 FUZZ_ENDPOINTS
- [ ] 新端点有对应的 SAMPLE_BODIES 定义
```

---

## 7. 新增端点的 Fuzzing 规则

在开发新 API 端点时，必须：

1. 将端点添加到 `FUZZ_ENDPOINTS` 列表（`test_api_fuzzing.py`）
2. 如果端点需要 body，在 `SAMPLE_BODIES` 中添加一个有效示例 body
3. 提交前运行 `pytest tests/fuzzing/ -v -m fuzzing` 确认通过

---

## 8. 已知限制

| 限制 | 说明 | 后续改进 |
|------|------|---------|
| 无状态感知 | Fuzzing payload 不依赖前置状态（如先创建再删除） | Phase 2 添加序列化场景 |
| 有限覆盖率 | 当前只覆盖 16 个核心端点（共 36+ 个 router） | 逐步扩展 |
| 同步 HTTP | 使用 httpx 同步 client | 保持当前模式 |
| 无内存检测 | 不检查内存泄漏或资源泄露 | Phase 2 添加 memray/valgrind |

---

## 9. 参考

- [OWASP Fuzzing](https://owasp.org/www-community/Fuzzing)
- [Pytest Parametrize](https://docs.pytest.org/en/stable/parametrize.html)
- [AI数字名片 契约测试规范](./CONTRACT_TESTING.md)
