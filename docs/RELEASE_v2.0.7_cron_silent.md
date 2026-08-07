# Cron脚本静默化 + graphql收集修复 v2.0.7

## 发布信息

| 项目 | 值 |
|:-----|:----|
| 版本标签 | `v2.0.7-cron-silent`（待 master 合并后打 tag） |
| 功能分支 | `feature/fix-cron-scripts` |
| 发布日期 | 2026-08-07 |
| 开发方式 | 远程分身（服务器）开发 → 补票合规流程 |
| 流程依据 | docs/全自动版本开发协议 v2.0 |

## 本次变更

### 1. 后端（FastAPI）— cron 脚本静默化
| 文件 | 变更 |
|:-----|:-----|
| `backend/scripts/disk_watchdog.py` | 磁盘正常时不输出（no_agent cron 空输出=不推送，消除每 5 分钟刷屏） |
| `backend/scripts/memory_pruner.py` | 无修剪动作/无错误时静默（空输出=不推送）；有动作才汇报 |

### 2. 测试基建
| 文件 | 变更 |
|:-----|:-----|
| `backend/tests/conftest.py` | 提前加载 `graphql.version` 子模块，修复全量收集期 `from graphql.version import` 解析失败（环境预存问题，Python 3.14 + graphql-core 3.2.11） |

### 3. 服务器适配遗留（Hermes cron 包装，随分支提交）
- `/opt/hermes-remote/home/scripts/disk_watchdog_wrapper.sh` — 由 Python 内容(.sh 后缀)重写为 bash 包装，修复 cron 报错
- `/opt/hermes-remote/home/scripts/memory_pruner_wrapper.sh` — 同上
- `/opt/hermes-remote/home/scripts/gaia_daily_brief.sh` — 读取记忆库内容时 iconv -c 过滤非法 UTF-8，修复 cron 解码失败

## 验证记录（服务器实测 2026-08-07）

| 验证项 | 结果 |
|:-----|:-----|
| disk_watchdog.py 语法+运行 | ✅ 语法 OK，正常态空输出（静默） |
| memory_pruner.py 语法+运行 | ✅ 语法 OK，无修剪空输出（静默） |
| 3 个 cron wrapper 脚本 | ✅ 全部 EXIT=0，简报正常输出 |
| graphql 测试 `tests/test_graphql.py` | ✅ 10/10 通过（修复前全量收集必失败） |
| API 契约门禁 `tests/test_api_standards.py` | ✅ 15/15 通过 |
| 服务健康 `curl :8201/health` | ✅ OK |
| 磁盘使用率 | ✅ 68%（WARN 阈值 80% 以下，无告警） |

## 已知限制

- `tests/contracts/` 契约测试套件存在**预存失败**（CSRF 403 + 部分 setup error），基线即有（ba33655 引入），非本次改动造成；本轮未纳入修复范围，后续单独处理
- 全量 pytest 有大量环境预存失败（Python 3.14 asyncio 兼容性，skill 已记载 868 过/271 败），门禁按规范跑 `-m "not db" --ignore=tests/test_graphql.py`

## 回滚方法

### 后端脚本
```bash
cd /var/www/ai-digital-card
git checkout master -- backend/scripts/disk_watchdog.py backend/scripts/memory_pruner.py
git checkout master -- backend/tests/conftest.py
```

### Hermes cron 包装
```bash
# 恢复旧版本（如需）：重新写入 Python 内容版本，或从 git 历史恢复
# 当前改动仅影响推送行为，不影响功能正确性
```

## 上线流程（等确认后执行）

```
feature/fix-cron-scripts → develop（Step1 确认）
develop → releaseV1.0（Step2 确认）
releaseV1.0 → master + tag v2.0.7-cron-silent（Step3 确认）
```
