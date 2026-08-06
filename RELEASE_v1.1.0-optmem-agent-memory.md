# RELEASE v1.1.0 — Agent 永久记忆服务（OptMem 原子化收割）

> 日期: 2026-08-06
> 分支: feature/optmem-agent-memory
> 上游: VictorTaelin/OptMem (⭐1122, 426-token 永久记忆方案)
> 定位: F-CARD-02 Agent 永久记忆能力（收割自 GitHub 爆火项目）

## 一、背景与动机

抖音视频「GitHub星探-OptMem_Agent永久记忆」展示了一个反直觉的 AI 记忆方案：

> 传统社区都在追向量数据库、追嵌入模型，VictorTaelin 站出来说：这些全都不需要。
> **文件系统就是最好的数据库，正则搜索就是最快的检索引擎，
> 280 字节的纯文本就是最可靠的记忆格式。**
> 100 万条记录，Wake 唤醒只要 0.03 秒。没有后台进程，没有任何东西在你不注意的时候运行。
> 换模型、换厂商，文件还在，记忆就在。

本版本将其**原子化 + feature 化**，落地为 AI数智名片 的产品能力。

## 二、原子化收割产物

### 1. `services/optmem_core.py` — OptMem 原子库（零依赖）
- 完整移植官方 CLI 核心（存储格式 100% 兼容，可混用）
- 面向对象 `OptMemStore`：`init/note/wake/recall/zoom/nap/forget/import/config`
- 纯标准库，无第三方依赖；结构化返回（dict），异常用 `OptMemError`
- 核心机制：
  - **固定宽度记录**（LOG_REC=320B）：位置即身份，O(1) seek，百万条唤醒 0.03s
  - **append-only LOG.txt**：唯一真相，永不编辑
  - **二叉树摘要 TREE/**：相邻记忆合并一行摘要，可随时从 LOG 重建
  - **文件锁**：多进程并行写入安全（id 在锁内分配）

### 2. `services/optmem_service.py` — 服务层
- 进程内单例；记忆库目录 `$AGENT_MEMORY_DIR` 可配
- 默认位置：`backend/data/agent_memory/`

### 3. `app/routers/memory_router.py` — API 路由

| 端点 | 方法 | 说明 |
|:-----|:-----|:-----|
| `/api/v1/memory/stats` | GET | 记忆库状态（条数/待压缩/配置）|
| `/api/v1/memory/wake` | GET | 唤醒：读取记忆上下文（树渲染）|
| `/api/v1/memory/note` | POST | 记一条记忆（≤280 字节）|
| `/api/v1/memory/recall?q=` | GET | 正则搜索全部历史记忆 |
| `/api/v1/memory/zoom?block=` | GET | 展开树节点到原始记忆 |
| `/api/v1/memory/nap` | POST | 提交压缩摘要（LLM 产出）|
| `/api/v1/memory/forget` | DELETE | 删除坏摘要（LOG 不动可重建）|

### 4. 配套修改
- `app/__init__.py`：注册 memory_router
- `app/middleware/api_version.py`：白名单加入 `/api/v1/memory`

## 三、验收记录

```
① GET  /api/v1/memory/stats          → 200 (memories:0)
② POST /api/v1/memory/note ×3        → 200 (id 0/1/2, 触发压缩提示)
③ GET  /api/v1/memory/wake           → 200 (3 行树渲染)
④ GET  /api/v1/memory/recall?q=向量   → 200 (hits:1)
⑤ POST /api/v1/memory/nap 0-1        → 200 (saved)
⑥ GET  /api/v1/memory/zoom?block=0-1 → 200 (两半展开)
⑦ 测试门禁 pytest test_api_standards → 15 passed
```

## 四、使用示例

```bash
# 记录一条记忆
curl -X POST /api/v1/memory/note -d '{"text":"客户A偏好每周五复盘"}'
# 唤醒（会话开始第一步）
curl /api/v1/memory/wake
# 搜索历史
curl "/api/v1/memory/recall?q=复盘"
```

## 五、设计哲学（继承 OptMem）

1. **无后台进程**：记忆只在被调用时读写，绝无隐藏运行
2. **零依赖**：一个 Python 文件，不绑定任何 AI 服务
3. **可移植**：`backend/data/agent_memory/` 拷走即带走全部记忆
4. **取舍明确**：不支持语义搜索（搜「苹果」不联想「水果」），换取极简与可靠

## 六、后续演进

- [ ] 接入盖娅知识蒸馏管线，自动将蒸馏结果写入记忆库
- [ ] 提供 /api/v1/memory/export 支持 Git 同步记忆
- [ ] 前端名片页展示「AI 记住了什么」（可管理/遗忘）
