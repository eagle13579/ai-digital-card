# AI 数字名片 — 变异测试指南

## 什么是变异测试 (Mutation Testing)？

变异测试通过**自动修改源代码**（例如将 `==` 改为 `!=`、将 `+` 改为 `-`、将 `True` 改为 `False`）生成"变异体"，然后运行测试用例：

- ✅ **变异体被杀 (Killed)**：测试发现了代码变化（测试有效）
- ❌ **变异体存活 (Survived)**：测试未发现变化（测试覆盖不足）

目标：**变异得分 ≥ 80%**，即至少 80% 的变异体被测试发现。

---

## 运行方式

### 1. 安装 mutmut

```bash
pip install mutmut
```

### 2. 运行变异测试

```bash
# 使用配置文件（推荐）
cd D:\\AI数智名片\\backend
mutmut run --paths-to-mutate app/services/ app/utils/ --tests-dir tests/

# 仅运行核心模块
mutmut run --paths-to-mutate app/services/matching_engine.py --tests-dir tests/
```

### 3. 查看结果

```bash
# 显示统计摘要
mutmut results

# 显示所有存活的变异体（需要改进测试的地方）
mutmut results --surviving-only

# 生成 HTML 报告
mutmut html
open html/index.html
```

---

## 解读结果

| 状态 | 含义 | 措施 |
|------|------|------|
| 🟢 **KILLED** | 变异体被测试杀死 | 测试有效 ✅ |
| 🔴 **SURVIVED** | 变异体存活 | 补充边界/异常测试用例 |
| ⏳ **TIMEOUT** | 测试超时 | 检查是否死循环或优化测试速度 |
| ⚪ **SKIPPED** | 跳过 | 检查配置 |

### 常见存活变异体及改进

| 变异类型 | 示例 | 改进方法 |
|----------|------|----------|
| 条件边界 | `a > b` → `a >= b` | 添加边界值测试 |
| 数值替换 | `0.5` → `0.499` | 测试浮点数精度边界 |
| 布尔反转 | `True` → `False` | 测试所有条件分支 |
| 空值检查 | 移除 `if x is None` | 测试 None 输入 |

---

## 持续集成

在 CI 中配置（.github/workflows/test.yml）：

```yaml
- name: Mutation Testing
  run: |
    pip install mutmut
    mutmut run --paths-to-mutate app/services/ --tests-dir tests/
    mutmut results | tee mutation_report.txt
    # 检查变异得分
    SCORE=$(grep -oP '\\d+\\.\\d+%' mutation_report.txt | head -1)
    echo "Mutation Score: $SCORE"
```

---

## 核心模块清单

| 模块 | 路径 | 优先级 |
|------|------|--------|
| 匹配引擎 | `app/services/matching_engine.py` | ⭐⭐⭐ |
| 标签服务 | `app/services/tag_service.py` | ⭐⭐⭐ |
| 画册服务 | `app/services/brochure.py` | ⭐⭐⭐ |
| 信任服务 | `app/services/trust_service.py` | ⭐⭐ |
| 格式化工具 | `app/utils/formatting.py` | ⭐⭐ |
