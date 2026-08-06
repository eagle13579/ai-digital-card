# AI数字名片 — 测试覆盖缺口分析

## 当前覆盖率: ~20% (81测试 / 402源文件)

## 模块级缺口

| 模块 | 源文件数 | 测试文件数 | 缺口评级 | 建议优先级 |
|------|---------|-----------|---------|-----------|
| ai/ (AI引擎) | 32 | 1 | 🟡 不足 | P0 (核心业务逻辑) |
| middleware/ | 19 | 0 | 🔴 严重 | P1 (安全关键) |
| routers/ | 58 | 2 | 🟡 不足 | P1 (API入口) |

## P0 建议: AI引擎测试优先

### 1. ai/vector_search.py (55,786行)
- 缺: 向量搜索单元测试
- 类型: 单元测试

### 2. ai/recommendation.py (50,758行)
- 缺: 推荐算法正确性测试
- 类型: 单元测试 + 集成测试

### 3. ai/gaia_evolution_brain.py (33,451行)
- 缺: 进化逻辑测试
- 类型: 单元测试

### 4. middleware/ (19个中间件)
- 缺: rate_limit, rbac, csrf, tenant 中间件测试
- 类型: 集成测试 (用TestClient)

## 快速提升方案

1. **AI引擎核心**: 为 vector_search, recommendation, rag_pipeline 各写1个核心测试 → 覆盖率+5%
2. **中间件**: 用 FastAPI TestClient 为 rate_limit, audit, security_headers 写集成测试 → 覆盖率+3%
3. **路由层**: 为 brochure, match, ai_assist 写端到端测试 → 覆盖率+5%
4. **K6压测**: 已有的 k6/ 目录完善压测场景 → 性能基线

目标: 从 20% → 50% (约需 120 个新测试)