# 军团共享学习协议 — 迁移指南（shared learning protocol）

> 版本: v1.0 | 2026-08-06 | 落地: AI数智名片 9 员工
> 目标: 任何多智能体项目实现「一人学会、全员共享」

## 是什么

让 N 个 Agent 组成的学习型组织：**任何员工学到新经验 → 全员共享 → 全员固化**。

```
员工A学到经验 → share_knowledge(title, content, tags)
                ├─ 1. 写入共享知识库（全员可检索）
                ├─ 2. 立即向量化（避免检索不到）
                └─ 3. 广播 knowledge.shared 事件
                            ↓
        其他 N-1 位员工订阅 handler → 自动 sync_knowledge()
                            ↓
        每员工每 30min cron 兜底同步 + 去重固化到各自 memory.db
```

## 三件套接口

| 组件 | 职责 | 实现位置（AI数智名片） |
|:-----|:-----|:-----|
| `share_knowledge` | 写库 + 向量化 + 广播 | `employee_profiles.py::_make_share_knowledge` |
| `sync_knowledge` | 拉最新 + 去重 + 写本地记忆 | `employee_profiles.py::_make_sync_knowledge` |
| `knowledge.shared` handler | 收到广播自动 sync | `employee_profiles.py::create_legion_agent` 步骤 8c |
| 30min cron | 兜底定时同步 | `create_legion_agent` 步骤 8d |

## 迁移步骤（新项目）

1. **复制模块**: `/var/www/liankebao/shared_learning.py`（通用实现，含 MIGRATION_CHECKLIST）
2. **实现 3 个接口**:
   - `SharedBrain`: ingest_knowledge / query_latest_shared / embed
   - `SharedEventBus`: publish
   - `LocalMemory`: remember / memorize
3. **Agent 工厂注册**（参考 create_legion_agent 步骤 8）:
   ```python
   agent.register_tool("share_knowledge", make_share_knowledge(...))
   agent.register_tool("sync_knowledge", make_sync_knowledge(...))
   agent.register_event_handler("knowledge.shared", make_shared_event_handler(...))
   agent.add_cron_job(CronJob("*/30 * * * *", make_sync_cron(sync_fn), "sync_knowledge_30min"))
   ```
4. **验证**:
   - share 返回 `{"success": true, "broadcast": true}`
   - 其他 Agent 日志出现「📚 收到共享知识广播」
   - 其他 Agent memory 库出现「[共享学习] <标题>」
   - 二次 sync 显示 skipped>0（去重生效）

## 五大坑（务必避开）

1. **广播必须走 runtime.dispatch_event()**（或直接 deliver 给 Agent 的 event_handlers）。仅 `event_bus.publish()` 只通知 subscribe() 注册的外部 handler，Agent 收不到！参考代码用 `get_runtime()` 获取 runtime 后调用 dispatch_event，再兜底 event_bus.publish。
2. **新知识必须立即向量化**。ingest 后 `vector_embedded=False`，语义检索查不到（向量搜索优先于全文搜索）。参考: `_embed_knowledge_batch(db, [knowledge])`。
3. **本地记忆库空文件会静默失败**。seed 生成的 memory.db 是 0 字节无表结构，`_write_memory_db` 必须自动建表（CREATE TABLE IF NOT EXISTS memories + 索引），否则员工永远没有持久记忆、去重失效。
4. **去重用完整标题**，不要 `title[:20]` 截断（写入内容前缀是 `[共享学习] `，前缀匹配会 miss）。
5. **sync 拉取直查数据库**（SELECT ... WHERE source LIKE 'agent_share%' ORDER BY created_at DESC），不要依赖另一个服务的语义检索 API——独立进程的内存向量索引是旧快照，查不到刚共享的知识。

## 配套（生产化建议）

- **防知识库污染**: 周期性状态类学习（如健康检查）只在状态变化时写入（`prev_overall != overall` 判断），否则每 5 分钟一条重复记录。
- **SRE 体检模式**: 每个组件检查「broker 失败 fall-through 到直连兜底」，不要 broker 失败就 return error（`Service 'cache' is not registered` 会让健康的 Redis 误报 error）。
- **AI Gateway 检查**: 用真实 LLM API ping（DeepSeekClient）代替「brain 内嵌 gateway + broker 服务」——后者在 embedding backend 场景永远拿不到 gateway。
